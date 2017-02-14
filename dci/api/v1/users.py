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
import uuid
from flask import json
from sqlalchemy import exc as sa_exc
from sqlalchemy import sql
from sqlalchemy import or_

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db.orm import dci_orm
from dci.db.orm import orm_utils

def _verify_existence_and_get_user(user_id):
    session = flask.g.db
    query = session.query(dci_orm.User)
    result = query.get(user_id)

    if result is None:
        raise dci_exc.DCIException('Resource "%s" not found.' % user_id,
                                   status_code=404)

    return result


@api.route('/users', methods=['POST'])
@auth.requires_auth
def create_users(user):
    created_at, updated_at = utils.get_dates(user)
    values = schemas.user.post(flask.request.json)

    args = schemas.args(flask.request.args.to_dict())

    session = flask.g.db

    if not(user.is_super_admin() or
           user.is_team_admin(values['team_id'])):
        raise auth.UNAUTHORIZED

    password_hash = auth.hash_password(values.get('password'))

    new_user = dci_orm.User()
    new_user.name = values['name']
    new_user.id = utils.gen_uuid()
    new_user.created_at = created_at
    new_user.updated_at = updated_at
    new_user.etag = utils.gen_etag()
    new_user.password = password_hash
    new_user.role = values.get('role', 'user')
    new_user.team_id = values['team_id']
    new_user.state = values['state']

    try:
        session.add(new_user)
        session.commit()
        session.flush()
    except sa_exc.IntegrityError:
        session.rollback()
        raise dci_exc.DCICreationConflict('User', 'name')

    # remove the password in the result for security reasons
    # del values['password']

    return flask.Response(
        json.dumps({'user': new_user.serialize}), 201,
        headers={'ETag': new_user.etag}, content_type='application/json'
    )


@api.route('/users', methods=['GET'])
@auth.requires_auth
def get_all_users(user, team_id=None):
    args = schemas.args(flask.request.args.to_dict())

    session = flask.g.db
    query = session.query(dci_orm.User)

    # If the user is not super admin limit the select to his team
    if not user.is_super_admin():
        query = query.filter(dci_orm.User.team_id == user.team_id)

    # So you'r super admin and you want a specific team
    elif team_id is not None and cur_user.is_super_admin():
        query = query.filter(dci_orm.User.team_id == team_id)

    # Normalize the query
    query = orm_utils.std_query(dci_orm.User, query, args)
    return flask.jsonify({'users': [i.serialize for i in query.all()],
                          '_meta': {'count': query.count()}})


@api.route('/users/<user_id>', methods=['GET'])
@auth.requires_auth
def get_user_by_id_or_name(user, user_id):
    args = schemas.args(flask.request.args.to_dict())

    session = flask.g.db
    query = session.query(dci_orm.User)

    # If it's not an admin, then get only the users of the caller's team
    if not user.is_super_admin():
        query = query.filter(dci_orm.User.team_id == user.team_id)

    query = query.filter(dci_orm.User.state != 'archived')
    try:
        uuid.UUID(user_id)
        query = query.filter(dci_orm.User.id == user_id)
    except:
        query = query.filter(dci_orm.User.name == user_id)

    if query.count() == 0:
        raise dci_exc.DCINotFound('User', user_id)

    result = query.first()

    res = flask.jsonify({'user': result.serialize})
    res.headers.add_header('ETag', result.etag)
    return res


@api.route('/users/<user_id>', methods=['PUT'])
@auth.requires_auth
def put_user(user, user_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    values = schemas.user.put(flask.request.json)

    session = flask.g.db

    puser = session.query(dci_orm.User).get(user_id)

    if puser.id != user_id:
        if not(user.is_super_admin() or
               user.is_team_admin(puser.team_id)):
            raise auth.UNAUTHORIZED

    if 'team_id' in values.keys() and not user.is_super_admin():
        raise auth.UNAUTHORIZED

    if 'role' in values.keys() and not user.is_team_admin(puser.team_id):
        raise auth.UNAUTHORIZED

    if not puser.etag == if_match_etag:
        raise dci_exc.DCIConflict('User', user_id)

    values['etag'] = utils.gen_etag()

    if 'password' in values:
        values['password'] = auth.hash_password(values.get('password'))

    for key, value in values.iteritems():
        setattr(puser, key, value)

    try:
        session.commit()
        session.flush()
    except:
        session.rollaback()
        raise dci_exc.DCIConflict('User', user_id)

    return flask.Response(None, 204, headers={'ETag': puser.etag},
                          content_type='application/json')


@api.route('/users/<user_id>', methods=['DELETE'])
@auth.requires_auth
def delete_user_by_id_or_name(user, user_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    session = flask.g.db

    duser = session.query(dci_orm.User).get(user_id)

    if not(user.is_super_admin() or
           user.is_team_admin(duser.team_id)):
        raise auth.UNAUTHORIZED

    if not duser.etag == if_match_etag:
        raise dci_exc.DCIDeleteConflict('User', user_id)

    duser.state = 'archived'
    try:
        session.commit()
        session.flush()
    except:
        raise dci_exc.DCIDeleteConflict('User', user_id)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/users/purge', methods=['GET'])
@auth.requires_auth
def get_to_purge_archived_users(user):
    return base.get_to_purge_archived_resources(user, _TABLE)


@api.route('/users/purge', methods=['POST'])
@auth.requires_auth
def purge_archived_users(user):
    return base.purge_archived_resources(user, _TABLE)
