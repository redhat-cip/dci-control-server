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
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import embeds
from dci.db import models


# associate column names with the corresponding SA Column object
_TABLE = models.USERS
_VALID_EMBED = embeds.users()
_USERS_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)

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
@auth.requires_auth
def create_users(user):
    values = v1_utils.common_values_dict(user)
    values.update(schemas.user.post(flask.request.json))

    if not(auth.is_admin(user) or auth.is_admin_user(user, values['team_id'])):
        raise auth.UNAUTHORIZED

    password_hash = auth.hash_password(values.get('password'))

    values.update({
        'password': password_hash,
        'role': values.get('role', 'user')
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
@auth.requires_auth
def get_all_users(user, team_id=None):
    args = schemas.args(flask.request.args.to_dict())
    embed = args['embed']

    q_bd = v1_utils.QueryBuilder(_TABLE, args['offset'], args['limit'],
                                 _VALID_EMBED)
    q_bd.select = list(_SELECT_WITHOUT_PASSWORD)
    q_bd.join(embed)

    q_bd.sort = v1_utils.sort_query(args['sort'], _USERS_COLUMNS,
                                    default='name')
    q_bd.where = v1_utils.where_query(args['where'], _TABLE, _USERS_COLUMNS)

    # If it's not an admin, then get only the users of the caller's team
    if not auth.is_admin(user):
        q_bd.where.append(_TABLE.c.team_id == user['team_id'])

    if team_id is not None:
        q_bd.where.append(_TABLE.c.team_id == team_id)

    q_bd.where.append(_TABLE.c.state != 'archived')

    # get the number of rows for the '_meta' section
    nb_row = flask.g.db_conn.execute(q_bd.build_nb_row()).scalar()
    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()
    rows = q_bd.dedup_rows(rows)

    return flask.jsonify({'users': rows, '_meta': {'count': nb_row}})


@api.route('/users/<uuid:user_id>', methods=['GET'])
@auth.requires_auth
def get_user_by_id(user, user_id):
    embed = schemas.args(flask.request.args.to_dict())['embed']

    q_bd = v1_utils.QueryBuilder(_TABLE, embed=_VALID_EMBED)
    q_bd.select = list(_SELECT_WITHOUT_PASSWORD)
    q_bd.join(embed)

    # If it's not an admin, then get only the users of the caller's team
    if not auth.is_admin(user):
        q_bd.where.append(_TABLE.c.team_id == user['team_id'])

    q_bd.where.append(
        sql.and_(
            _TABLE.c.state != 'archived',
            _TABLE.c.id == user_id
        )
    )

    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()
    rows = q_bd.dedup_rows(rows)
    if len(rows) != 1:
        raise dci_exc.DCINotFound('User', user_id)
    guser = rows[0]

    res = flask.jsonify({'user': guser})
    res.headers.add_header('ETag', guser['etag'])
    return res


@api.route('/users/<uuid:user_id>', methods=['PUT'])
@auth.requires_auth
def put_user(user, user_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    values = schemas.user.put(flask.request.json)

    puser = dict(_verify_existence_and_get_user(user_id))

    if puser['id'] != str(user_id):
        if not(auth.is_admin(user) or
               auth.is_admin_user(user, puser['team_id'])):
            raise auth.UNAUTHORIZED

    # TODO(yassine): if the user wants to change the team, then check its done
    # by a super admin. ie. team_name='admin'

    values['etag'] = utils.gen_etag()

    if 'password' in values:
        values['password'] = auth.hash_password(values.get('password'))

    where_clause = sql.and_(
        _TABLE.c.etag == if_match_etag,
        _TABLE.c.id == user_id
    )
    query = _TABLE.update().where(where_clause).values(**values)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict('User', user_id)

    return flask.Response(None, 204, headers={'ETag': values['etag']},
                          content_type='application/json')


@api.route('/users/<uuid:user_id>', methods=['DELETE'])
@auth.requires_auth
def delete_user_by_id_or_name(user, user_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    duser = _verify_existence_and_get_user(user_id)

    if not(auth.is_admin(user) or
           auth.is_admin_user(user, duser['team_id'])):
        raise auth.UNAUTHORIZED

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
@auth.requires_auth
@auth.requires_platform_admin
def get_to_purge_archived_users(user):
    return base.get_to_purge_archived_resources(user, _TABLE)


@api.route('/users/purge', methods=['POST'])
@auth.requires_auth
@auth.requires_platform_admin
def purge_archived_users(user):
    return base.purge_archived_resources(user, _TABLE)
