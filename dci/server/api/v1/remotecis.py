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
from dci.server.common import exceptions
from dci.server.common import schemas
from dci.server.common import utils
from dci.server.db import models_core as models


# associate column names with the corresponding SA Column object
_R_COLUMNS = v1_utils.get_columns_name_with_objects(models.REMOTECIS)
_VALID_EMBED = {'team': models.TEAMS}


def _verify_existence_and_get_remoteci(r_id):
    return v1_utils.verify_existence_and_get(
        [models.REMOTECIS], r_id,
        sqlalchemy.sql.or_(models.REMOTECIS.c.id == r_id,
                           models.REMOTECIS.c.name == r_id))


@api.route('/remotecis', methods=['POST'])
@auth2.requires_auth
def create_remotecis():
    values = schemas.remoteci.post(flask.request.json)
    etag = utils.gen_etag()
    values.update(
        {'id': utils.gen_uuid(),
         'created_at': datetime.datetime.utcnow().isoformat(),
         'updated_at': datetime.datetime.utcnow().isoformat(),
         'data': values.get('data', {}),
         'etag': etag}
    )

    query = models.REMOTECIS.insert().values(**values)

    flask.g.db_conn.execute(query)

    return flask.Response(
        json.dumps({'remoteci': values}), 201,
        headers={'ETag': etag}, content_type='application/json'
    )


@api.route('/remotecis', methods=['GET'])
@auth2.requires_auth
def get_all_remotecis(t_id=None):
    args = schemas.args(flask.request.args.to_dict())
    # convenient alias
    embed = args['embed']

    query = sqlalchemy.sql.select([models.REMOTECIS])

    if embed:
        query = v1_utils.get_query_with_join(models.REMOTECIS,
                                             [models.REMOTECIS], embed,
                                             _VALID_EMBED)

    query = v1_utils.sort_query(query, args['sort'], _R_COLUMNS)
    query = v1_utils.where_query(query, args['where'], models.REMOTECIS,
                                 _R_COLUMNS)
    query = query.limit(args['limit']).offset(args['offset'])

    # used for counting the number of rows when ct_id is not None
    where_t_cond = None
    if t_id is not None:
        where_t_cond = models.REMOTECIS.c.team_id == t_id
        query = query.where(where_t_cond)

    nb_remotecis = utils.get_number_of_rows(models.REMOTECIS, where_t_cond)

    rows = flask.g.db_conn.execute(query).fetchall()
    result = [v1_utils.group_embedded_resources(embed, row) for row in rows]

    result = {'remotecis': result, '_meta': {'count': nb_remotecis}}
    result = json.dumps(result, default=utils.json_encoder)
    return flask.Response(result, 200, content_type='application/json')


@api.route('/remotecis/<r_id>', methods=['GET'])
@auth2.requires_auth
def get_remoteci_by_id_or_name(r_id):
    embed = schemas.args(flask.request.args.to_dict())['embed']
    v1_utils.verify_embed_list(embed, _VALID_EMBED.keys())

    # the default query with no parameters
    query = sqlalchemy.sql.select([models.REMOTECIS])

    # if embed then construct the query with a join
    if embed:
        query = v1_utils.get_query_with_join(models.REMOTECIS,
                                             [models.REMOTECIS], embed,
                                             _VALID_EMBED)

    query = query.where(
        sqlalchemy.sql.or_(models.REMOTECIS.c.id == r_id,
                           models.REMOTECIS.c.name == r_id))

    row = flask.g.db_conn.execute(query).fetchone()
    remoteci = v1_utils.group_embedded_resources(embed, row)

    if row is None:
        raise dci_exc.DCIException("Remoteci '%s' not found." % r_id,
                                   status_code=404)

    etag = remoteci['etag']
    remoteci = json.dumps({'remoteci': remoteci}, default=utils.json_encoder)
    return flask.Response(remoteci, 200, headers={'ETag': etag},
                          content_type='application/json')


@api.route('/remotecis/<r_id>', methods=['PUT'])
@auth2.requires_auth
def put_remoteci(r_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    data_json = flask.request.json
    # verif put

    _verify_existence_and_get_remoteci(r_id)

    data_json['etag'] = utils.gen_etag()
    query = models.REMOTECIS.update().where(
        sqlalchemy.sql.and_(
            sqlalchemy.sql.or_(models.REMOTECIS.c.id == r_id,
                               models.REMOTECIS.c.name == r_id),
            models.REMOTECIS.c.etag == if_match_etag)).values(**data_json)

    result = flask.g.db_conn.execute(query)

    if result.rowcount == 0:
        raise exceptions.DCIException("Conflict on test '%s' or etag "
                                      "not matched." % r_id, status_code=409)

    return flask.Response(None, 204, headers={'ETag': data_json['etag']},
                          content_type='application/json')


@api.route('/remotecis/<r_id>', methods=['DELETE'])
@auth2.requires_auth
def delete_remoteci_by_id_or_name(r_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    _verify_existence_and_get_remoteci(r_id)

    query = models.REMOTECIS.delete().where(
        sqlalchemy.sql.and_(
            sqlalchemy.sql.or_(models.REMOTECIS.c.id == r_id,
                               models.REMOTECIS.c.name == r_id),
            models.REMOTECIS.c.etag == if_match_etag))

    result = flask.g.db_conn.execute(query)

    if result.rowcount == 0:
        raise exceptions.DCIException("Test '%s' already deleted or "
                                      "etag not matched." % r_id,
                                      status_code=409)

    return flask.Response(None, 204, content_type='application/json')
