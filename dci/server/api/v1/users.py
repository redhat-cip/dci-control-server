# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Red Hat, Inc
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

import datetime

import flask
from flask import json
import sqlalchemy.sql

from dci.server.api.v1 import api
from dci.server.api.v1 import utils as v1_utils
from dci.server import auth2
from dci.server.common import exceptions as dci_exc
from dci.server.common import schemas
from dci.server.common import utils
from dci.server.db import models_core as models


# associate column names with the corresponding SA Column object
_USERS_COLUMNS = v1_utils.get_columns_name_with_objects(models.USERS)
_VALID_EMBED = {'team': models.TEAMS}

# select without the password column for security reasons
_SELECT_WITHOUT_PASSWORD = [models.USERS.c[c_name]
                            for c_name in models.USERS.c.keys()
                            if c_name != 'password']


def _verify_existence_and_get_user(user_id):
    return v1_utils.verify_existence_and_get(
        _SELECT_WITHOUT_PASSWORD, user_id,
        sqlalchemy.sql.or_(models.USERS.c.id == user_id,
                           models.USERS.c.name == user_id))


@api.route('/users', methods=['POST'])
@auth2.requires_auth(auth2.ADMIN)
def create_users(user_info):
    values = schemas.user.post(flask.request.json)

    auth2.check_super_admin_or_same_team(user_info, values['team_id'])

    etag = utils.gen_etag()
    password_hash = auth2.hash_password(values.get('password'))

    values.update({
        'id': utils.gen_uuid(),
        'created_at': datetime.datetime.utcnow().isoformat(),
        'updated_at': datetime.datetime.utcnow().isoformat(),
        'etag': etag,
        'password': password_hash
    })

    query = models.USERS.insert().values(**values)

    flask.g.db_conn.execute(query)
    # remove the password in the result for security reasons
    del values['password']

    return flask.Response(
        json.dumps({'user': values}), 201,
        headers={'ETag': etag}, content_type='application/json'
    )


@api.route('/users', methods=['GET'])
@auth2.requires_auth()
def get_all_users(user_info, team_id=None):
    args = schemas.args(flask.request.args.to_dict())
    embed = args['embed']

    query = sqlalchemy.sql.select(_SELECT_WITHOUT_PASSWORD)

    #  If it's not an admin, then get only the users of the caller's team
    if user_info.role != auth2.SUPER_ADMIN:
        query = query.where(models.USERS.c.team_id == user_info.team)

    # if embed then construct the query with a join
    if embed:
        query = v1_utils.get_query_with_join(models.USERS,
                                             _SELECT_WITHOUT_PASSWORD, embed,
                                             _VALID_EMBED)
    query = v1_utils.sort_query(query, args['sort'], _USERS_COLUMNS)
    query = v1_utils.where_query(query, args['where'], models.USERS,
                                 _USERS_COLUMNS)

    # used for counting the number of rows when ct_id is not None
    where_t_cond = None
    if team_id is not None:
        where_t_cond = models.USERS.c.team_id == team_id
        query = query.where(where_t_cond)

    if args['limit'] is not None:
        query = query.limit(args['limit'])

    if args['offset'] is not None:
        query = query.offset(args['offset'])

    nb_users = utils.get_number_of_rows(models.USERS, where_t_cond)

    rows = flask.g.db_conn.execute(query).fetchall()
    result = [v1_utils.group_embedded_resources(embed, row) for row in rows]

    result = {'users': result, '_meta': {'count': nb_users}}
    result = json.dumps(result, default=utils.json_encoder)
    return flask.Response(result, 200, content_type='application/json')


@api.route('/users/<user_id>', methods=['GET'])
@auth2.requires_auth()
def get_user_by_id_or_name(user_info, user_id):
    args = schemas.args(flask.request.args.to_dict())
    embed = args['embed']

    # the default query with no parameters
    query = sqlalchemy.sql.select(_SELECT_WITHOUT_PASSWORD)

    # If it's not an admin, then get only the users of the caller's team
    if user_info.role != auth2.SUPER_ADMIN:
        query = query.where(models.USERS.c.team_id == user_info.team)

    if embed:
        query = v1_utils.get_query_with_join(models.USERS,
                                             _SELECT_WITHOUT_PASSWORD, embed,
                                             _VALID_EMBED)

    query = query.where(sqlalchemy.sql.or_(models.USERS.c.id == user_id,
                                           models.USERS.c.name == user_id))

    row = flask.g.db_conn.execute(query).fetchone()
    user = v1_utils.group_embedded_resources(embed, row)

    if row is None:
        raise dci_exc.DCIException("User '%s' not found." % user_id,
                                   status_code=404)

    etag = user['etag']
    user = json.dumps({'user': user}, default=utils.json_encoder)
    return flask.Response(user, 200, headers={'ETag': etag},
                          content_type='application/json')


@api.route('/users/<user_id>', methods=['PUT'])
@auth2.requires_auth(auth2.ADMIN)
def put_user(user_info, user_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    print('if_match_etag %s' % if_match_etag)
    values = schemas.user.put(flask.request.json)

    user = dict(_verify_existence_and_get_user(user_id))

    # If the user's not an admin, then he is not allowed to update a user
    auth2.check_super_admin_or_same_team(user_info, user['team_id'])

    # TODO(yassine): if the user wants to change the team, then check its done
    # by a super admin. ie. team=dci_config.TEAM_ADMIN_ID.

    values['etag'] = utils.gen_etag()

    if 'password' in values:
        values['password'] = auth2.hash_password(values.get('password'))

    query = models.USERS.update().where(
        sqlalchemy.sql.and_(
            sqlalchemy.sql.or_(models.USERS.c.id == user_id,
                               models.USERS.c.name == user_id),
            models.USERS.c.etag == if_match_etag)).values(**values)

    result = flask.g.db_conn.execute(query)

    if result.rowcount == 0:
        raise dci_exc.DCIException("Conflict on user '%s' or etag "
                                   "not matched." % user_id,
                                   status_code=409)

    return flask.Response(None, 204, headers={'ETag': values['etag']},
                          content_type='application/json')


@api.route('/users/<user_id>', methods=['DELETE'])
@auth2.requires_auth(auth2.ADMIN)
def delete_user_by_id_or_name(user_info, user_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    user = _verify_existence_and_get_user(user_id)

    # If the user's not an admin, then he is not allowed to create a new user
    auth2.check_super_admin_or_same_team(user_info, user['team_id'])

    query = models.USERS.delete().where(
        sqlalchemy.sql.and_(
            sqlalchemy.sql.or_(models.USERS.c.id == user_id,
                               models.USERS.c.name == user_id),
            models.USERS.c.etag == if_match_etag))

    result = flask.g.db_conn.execute(query)

    if result.rowcount == 0:
        raise dci_exc.DCIException("User '%s' already deleted or "
                                   "etag not matched." % user_id,
                                   status_code=409)

    return flask.Response(None, 204, content_type='application/json')
