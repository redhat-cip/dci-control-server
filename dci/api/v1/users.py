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
from sqlalchemy import sql

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import embeds
from dci.db import models


# associate column names with the corresponding SA Column object
_TABLE = models.USERS
_VALID_EMBED = embeds.users()
_USERS_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)
_EMBED_MANY = {
    'team': False,
    'role': False,
    'remotecis': True,
}

# select without the password column for security reasons
_SELECT_WITHOUT_PASSWORD = [
    _TABLE.c[c_name] for c_name in _TABLE.c.keys() if c_name != 'password'
]


def _verify_existence_and_get_user(user_id):
    where_clause = _TABLE.c.id == user_id
    query = sql.select(_SELECT_WITHOUT_PASSWORD).where(where_clause)
    result = flask.g.db_conn.execute(query).fetchone()

    if result is None:
        raise dci_exc.DCIException('Resource "%s" not found.' % user_id,
                                   status_code=404)

    return result


@api.route('/users', methods=['POST'])
@decorators.login_required
@decorators.check_roles
def create_users(user):
    values = v1_utils.common_values_dict()
    values.update(schemas.user.post(flask.request.json))

    if values.get('team_id'):
        if not user.is_in_team(values['team_id']):
            raise dci_exc.Unauthorized()

    role_id = values.get('role_id', auth.get_role_id('USER'))
    if user.is_not_super_admin() and \
            (role_id == auth.get_role_id('SUPER_ADMIN') or
             role_id == auth.get_role_id('READ_ONLY_USER')):
        raise dci_exc.Unauthorized()

    values.update({
        'password': auth.hash_password(values.get('password')),
        'role_id': role_id,
        'fullname': values.get('fullname', values['name']),
        'timezone': values.get('timezone', 'UTC'),
        'sso_username': None
    })

    query = _TABLE.insert().values(**values)

    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(_TABLE.name, 'name')

    # remove the password in the result for security reasons
    del values['password']

    return flask.Response(
        json.dumps({'user': values}), 201,
        headers={'ETag': values['etag']}, content_type='application/json'
    )


@api.route('/users', methods=['GET'])
@decorators.login_required
@decorators.check_roles
def get_all_users(user, team_id=None):
    args = schemas.args(flask.request.args.to_dict())
    query = v1_utils.QueryBuilder(_TABLE, args, _USERS_COLUMNS, ['password'])

    if user.is_not_super_admin():
        query.add_extra_condition(_TABLE.c.team_id.in_(user.teams_ids))

    if team_id is not None:
        query.add_extra_condition(_TABLE.c.team_id == team_id)

    query.add_extra_condition(_TABLE.c.state != 'archived')

    # get the number of rows for the '_meta' section
    nb_rows = query.get_number_of_rows()
    rows = query.execute(fetchall=True)
    rows = v1_utils.format_result(rows, _TABLE.name, args['embed'],
                                  _EMBED_MANY)

    return flask.jsonify({'users': rows, '_meta': {'count': nb_rows}})


def user_by_id(user, user_id):
    user_res = v1_utils.verify_existence_and_get(user_id, _TABLE)
    return base.get_resource_by_id(user, user_res, _TABLE, _EMBED_MANY,
                                   ignore_columns=['password'])


@api.route('/users/<uuid:user_id>', methods=['GET'])
@decorators.login_required
@decorators.check_roles
def get_user_by_id(user, user_id):
    return user_by_id(user, user_id)


@api.route('/users/me', methods=['GET'])
@decorators.login_required
@decorators.check_roles
def get_current_user(user):
    return user_by_id(user, user['id'])


@api.route('/users/me', methods=['PUT'])
@decorators.login_required
@decorators.check_roles
def put_current_user(user):
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    values = schemas.current_user.put(flask.request.json)

    if user.is_not_read_only_user():
        current_password = values['current_password']
        encrypted_password = user['password']
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
                       'fullname': values.get('fullname') or user['fullname'],
                       'email': values.get('email') or user['email'],
                       'timezone': values.get('timezone') or user['timezone']})

    query = _TABLE.update().returning(*_TABLE.columns).where(sql.and_(
        _TABLE.c.etag == if_match_etag,
        _TABLE.c.id == user['id']
    )).values(new_values)

    result = flask.g.db_conn.execute(query)
    if not result.rowcount:
        raise dci_exc.DCIConflict('User', user['id'])
    _result = dict(result.fetchone())
    del _result['password']

    return flask.Response(
        json.dumps({'user': _result}), 200, headers={'ETag': etag},
        content_type='application/json'
    )


@api.route('/users/<uuid:user_id>', methods=['PUT'])
@decorators.login_required
@decorators.check_roles
def put_user(user, user_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    values = schemas.user.put(flask.request.json)

    # to update a user the caller must be either the admin of its team
    # or a super admin
    puser = dict(_verify_existence_and_get_user(user_id))
    if puser['id'] != str(user_id) and not user.is_in_team(puser['team_id']):
        raise dci_exc.Unauthorized()

    # if the caller wants to update the team_id then it must be done by a super
    # admin
    if 'team_id' in values and user.is_not_super_admin() and \
       not user.is_team_product_owner(values['team_id']):
        raise dci_exc.Unauthorized()

    values['etag'] = utils.gen_etag()

    if 'password' in values:
        values['password'] = auth.hash_password(values.get('password'))

    where_clause = sql.and_(
        _TABLE.c.etag == if_match_etag,
        _TABLE.c.id == user_id
    )
    query = _TABLE.update().returning(*_TABLE.columns).\
        where(where_clause).values(**values)

    result = flask.g.db_conn.execute(query)
    if not result.rowcount:
        raise dci_exc.DCIConflict('User', user_id)

    _result = dict(result.fetchone())
    del _result['password']

    return flask.Response(
        json.dumps({'user': _result}), 200, headers={'ETag': values['etag']},
        content_type='application/json'
    )


@api.route('/users/<uuid:user_id>', methods=['DELETE'])
@decorators.login_required
@decorators.check_roles
def delete_user_by_id(user, user_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    duser = _verify_existence_and_get_user(user_id)

    if user.is_not_in_team(duser['team_id']):
        raise dci_exc.Unauthorized()

    values = {'state': 'archived'}
    where_clause = sql.and_(
        _TABLE.c.etag == if_match_etag,
        _TABLE.c.id == user_id
    )
    query = _TABLE.update().where(where_clause).values(**values)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIDeleteConflict('User', user_id)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/users/purge', methods=['GET'])
@decorators.login_required
@decorators.check_roles
def get_to_purge_archived_users(user):
    return base.get_to_purge_archived_resources(user, _TABLE)


@api.route('/users/purge', methods=['POST'])
@decorators.login_required
@decorators.check_roles
def purge_archived_users(user):
    return base.purge_archived_resources(user, _TABLE)
