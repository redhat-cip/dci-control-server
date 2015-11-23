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
from dci.server.common import exceptions
from dci.server.common import schemas
from dci.server.common import utils
from dci.server.db import models_core as models


# associate column names with the corresponding SA Column object
_USERS_COLUMNS = v1_utils.get_columns_name_with_objects(models.USERS)
_VALID_EMBED = {'team': models.TEAMS}


def _verify_existence_and_get_user(user_id):
    return v1_utils.verify_existence_and_get(
        models.USERS, user_id,
        sqlalchemy.sql.or_(models.USERS.c.id == user_id,
                           models.USERS.c.name == user_id))


@api.route('/users', methods=['POST'])
def create_users():
    values = schemas.user.post(flask.request.json)
    etag = utils.gen_etag()
    values.update(
        {'id': utils.gen_uuid(),
         'created_at': datetime.datetime.utcnow().isoformat(),
         'updated_at': datetime.datetime.utcnow().isoformat(),
         'etag': etag}
    )

    query = models.USERS.insert().values(**values)

    flask.g.db_conn.execute(query)

    return flask.Response(
        json.dumps({'user': values}), 201,
        headers={'ETag': etag}, content_type='application/json'
    )


@api.route('/users', methods=['GET'])
def get_all_users(team_id=None):
    args = schemas.args(flask.request.args.to_dict())
    embed = args['embed']

    query = sqlalchemy.sql.select([models.USERS])

    # if embed then construct the query with a join
    if embed:
        query = v1_utils.get_query_with_join(models.COMPONENTS, embed,
                                             _VALID_EMBED)
    query = v1_utils.sort_query(query, args['sort'], _USERS_COLUMNS)
    query = v1_utils.where_query(query, args['where'], models.USERS,
                                 _USERS_COLUMNS)

    # used for counting the number of rows when ct_id is not None
    where_t_cond = None
    if team_id is not None:
        where_t_cond = models.USERS.c.team_id == team_id
        query = query.where(where_t_cond)

    query = query.limit(args['limit']).offset(args['offset'])

    nb_users = utils.get_number_of_rows(models.USERS, where_t_cond)

    rows = flask.g.db_conn.execute(query).fetchall()
    result = [dict(row) for row in rows]

    result = {'users': result, '_meta': {'count': nb_users}}
    result = json.dumps(result, default=utils.json_encoder)
    return flask.Response(result, 200, content_type='application/json')


@api.route('/users/<user_id>', methods=['GET'])
def get_user_by_id_or_name(user_id):
    user = _verify_existence_and_get_user(user_id)
    etag = user['etag']
    user = json.dumps({'user': dict(user)}, default=utils.json_encoder)
    return flask.Response(user, 200, headers={'ETag': etag},
                          content_type='application/json')


@api.route('/users/<user_id>', methods=['PUT'])
def put_user(user_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    data_json = schemas.user.put(flask.request.json)

    _verify_existence_and_get_user(user_id)

    data_json['etag'] = utils.gen_etag()
    query = models.USERS.update().where(
        sqlalchemy.sql.and_(
            sqlalchemy.sql.or_(models.USERS.c.id == user_id,
                               models.USERS.c.name == user_id),
            models.USERS.c.etag == if_match_etag)).values(**data_json)

    result = flask.g.db_conn.execute(query)

    if result.rowcount == 0:
        raise exceptions.DCIException("Conflict on user '%s' or etag "
                                      "not matched." % user_id,
                                      status_code=409)

    return flask.Response(None, 204, headers={'ETag': data_json['etag']},
                          content_type='application/json')


@api.route('/users/<user_id>', methods=['DELETE'])
def delete_user_by_id_or_name(user_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    _verify_existence_and_get_user(user_id)

    query = models.USERS.delete().where(
        sqlalchemy.sql.and_(
            sqlalchemy.sql.or_(models.USERS.c.id == user_id,
                               models.USERS.c.name == user_id),
            models.USERS.c.etag == if_match_etag))

    result = flask.g.db_conn.execute(query)

    if result.rowcount == 0:
        raise exceptions.DCIException("User '%s' already deleted or "
                                      "etag not matched." % user_id,
                                      status_code=409)

    return flask.Response(None, 204, content_type='application/json')
