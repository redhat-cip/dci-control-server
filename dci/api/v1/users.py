# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Red Hat, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import flask
from flask import json
from sqlalchemy import exc as sa_exc
import sqlalchemy.orm as sa_orm

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common import utils
from dci.db import declarative as d
from dci.db import models
from dci.db import models2
from dci.common.schemas import (
    check_json_is_valid,
    clean_json_with_schema,
    create_user_schema,
    update_user_schema,
    update_current_user_schema,
    check_and_get_args
)

_TABLE = models.USERS
_USERS_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)
_EMBED_MANY = {
    'team': True,
    'remotecis': True,
}


@api.route('/users', methods=['POST'])
@decorators.login_required
def create_users(user):
    values = flask.request.json
    check_json_is_valid(create_user_schema, values)
    values.update(v1_utils.common_values_dict())

    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    values.update({
        'password': auth.hash_password(values.get('password')),
        'fullname': values.get('fullname', values['name']),
        'timezone': values.get('timezone', 'UTC'),
        'sso_username': None
    })

    try:
        u = models2.User(**values)
        u_serialized = u.serialize()
        flask.g.session.add(u)
        flask.g.session.commit()
    except sa_exc.IntegrityError as ie:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message=str(ie), status_code=409)
    except Exception as e:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message=str(e))

    return flask.Response(
        json.dumps({'user': u_serialized}), 201,
        headers={'ETag': values['etag']}, content_type='application/json'
    )


@api.route('/users', methods=['GET'])
@decorators.login_required
def get_all_users(user):
    args = check_and_get_args(flask.request.args.to_dict())
    if user.is_not_super_admin() and user.is_not_epm():
        raise dci_exc.Unauthorized()

    q = flask.g.session.query(models2.User).\
        filter(models2.User.state != 'archived').\
        options(sa_orm.joinedload('team')).\
        options(sa_orm.joinedload('remotecis'))
    q = d.handle_args(q, models2.User, args)
    nb_users = q.count()
    q = d.handle_pagination(q, args)
    users = q.all()
    users = list(map(lambda u: u.serialize(ignore_columns=('password', 'remotecis.api_secret')), users))

    return flask.jsonify({'users': users, '_meta': {'count': nb_users}})


def user_by_id(user, user_id):
    if user.id != user_id and user.is_not_super_admin() and user.is_not_epm():
        raise dci_exc.Unauthorized()
    v1_utils.verify_existence_and_get(user_id, _TABLE)

    u = flask.g.session.query(models2.User).\
        filter(models2.User.state != 'archived').\
        filter(models2.User.id == user_id).\
        options(sa_orm.joinedload('team')).\
        options(sa_orm.joinedload('remotecis')).one()
    if not u:
        raise dci_exc.DCIException(message="user not found", status_code=404)

    return flask.Response(
        json.dumps({'user': u.serialize(ignore_columns=('password',))}), 200, headers={'ETag': u.etag},
        content_type='application/json')


@api.route('/users/<uuid:user_id>', methods=['GET'])
@decorators.login_required
def get_user_by_id(user, user_id):
    return user_by_id(user, str(user_id))


@api.route('/users/me', methods=['GET'])
@decorators.login_required
def get_current_user(user):
    return user_by_id(user, user.id)


@api.route('/users/me', methods=['PUT'])
@decorators.login_required
def put_current_user(user):
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    values = clean_json_with_schema(update_current_user_schema, flask.request.json)

    if user.is_not_read_only_user():
        current_password = values['current_password']
        encrypted_password = user.password
        if not auth.check_passwords_equal(current_password,
                                          encrypted_password):
            raise dci_exc.DCIException('current_password invalid')

    new_values = {}
    new_password = values.get('new_password')
    if new_password:
        encrypted_password = auth.hash_password(new_password)
        new_values['password'] = encrypted_password

    etag = utils.gen_etag()
    new_values.update({'etag': etag,
                       'fullname': values.get('fullname') or user.fullname,
                       'email': values.get('email') or user.email,
                       'timezone': values.get('timezone') or user.timezone})

    updated_user = flask.g.session.query(models2.User).\
        filter(models2.User.id == user.id).\
        filter(models2.User.etag == if_match_etag).\
        update(new_values)
    flask.g.session.commit()

    if not updated_user:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message="update failed, either user not found or etag not matched", status_code=409)

    u = flask.g.session.query(models2.User).filter(models2.User.id == user.id).one()
    if not u:
        raise dci_exc.DCIException(message="unable to return user", status_code=400)

    return flask.Response(
        json.dumps({'user': u.serialize(ignore_columns=('password',))}), 200, headers={'ETag': etag},
        content_type='application/json')


@api.route('/users/<uuid:user_id>', methods=['PUT'])
@decorators.login_required
def put_user(user, user_id):
    values = clean_json_with_schema(update_user_schema, flask.request.json)
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    # to update a user the caller must be a super admin
    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    values['etag'] = utils.gen_etag()

    if 'password' in values:
        values['password'] = auth.hash_password(values.get('password'))

    updated_user = flask.g.session.query(models2.User).\
        filter(models2.User.id == user_id).\
        filter(models2.User.etag == if_match_etag).\
        update(values)
    flask.g.session.commit()

    if not updated_user:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message="update failed, either user not found or etag not matched", status_code=409)

    u = flask.g.session.query(models2.User).filter(models2.User.id == user_id).one()
    if not u:
        raise dci_exc.DCIException(message="unable to return user", status_code=400)

    return flask.Response(
        json.dumps({'user': u.serialize(ignore_columns=('password',))}), 200, headers={'ETag': values['etag']},
        content_type='application/json'
    )


@api.route('/users/<uuid:user_id>', methods=['DELETE'])
@decorators.login_required
def delete_user_by_id(user, user_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    v1_utils.verify_existence_and_get(user_id, _TABLE)

    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    deleted_user = flask.g.session.query(models2.User).\
        filter(models2.User.id == user_id).\
        filter(models2.User.etag == if_match_etag).\
        update({'state': 'archived'})
    flask.g.session.commit()

    if not deleted_user:
        raise dci_exc.DCIException(message="delete failed, either user already deleted or etag not matched", status_code=409)

    return flask.Response(None, 204, content_type='application/json')


@api.route("/users/<uuid:user_id>/remotecis", methods=["GET"])
@decorators.login_required
def get_subscribed_remotecis(identity, user_id):
    if (identity.is_not_super_admin() and identity.id != str(user_id)
        and identity.is_not_epm()):
        raise dci_exc.Unauthorized()

    q = flask.g.session.query(models2.User).\
        filter(models2.User.id == user_id).\
        filter(models2.User.state != 'archived').\
        options(sa_orm.joinedload('remotecis'))
    user = q.one()
    user = user.serialize(ignore_columns=('remotecis.api_secret'))

    return flask.Response(
        json.dumps({"remotecis": user.get('remotecis')}), 200, content_type="application/json"
    )


@api.route('/users/purge', methods=['GET'])
@decorators.login_required
def get_to_purge_archived_users(user):
    return base.get_to_purge_archived_resources(user, _TABLE)


@api.route('/users/purge', methods=['POST'])
@decorators.login_required
def purge_archived_users(user):
    return base.purge_archived_resources(user, _TABLE)
