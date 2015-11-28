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
_JS_COLUMNS = v1_utils.get_columns_name_with_objects(models.JOBSTATES)
_VALID_EMBED = {'job': models.JOBS,
                'team': models.TEAMS}


def _verify_existence_and_get_jobstate(js_id):
    return v1_utils.verify_existence_and_get(
        [models.JOBSTATES], js_id, models.JOBSTATES.c.id == js_id)


@api.route('/jobstates', methods=['POST'])
@auth2.requires_auth()
def create_jobstates(user_info):
    values = schemas.jobstate.post(flask.request.json)

    # If it's not a super admin nor belongs to the same team_id
    auth2.check_super_admin_or_same_team(user_info, values['team_id'])

    etag = utils.gen_etag()
    values.update({
        'id': utils.gen_uuid(),
        'created_at': datetime.datetime.utcnow().isoformat(),
        'updated_at': datetime.datetime.utcnow().isoformat(),
        'etag': etag
    })

    query = models.JOBSTATES.insert().values(**values)

    flask.g.db_conn.execute(query)

    result = json.dumps({'jobstate': values})
    return flask.Response(result, 201, headers={'ETag': etag},
                          content_type='application/json')


@api.route('/jobstates/<js_id>', methods=['PUT'])
@auth2.requires_auth()
def put_jobstate(user_info, js_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    values = schemas.jobstate.put(flask.request.json)

    jobstate = dict(_verify_existence_and_get_jobstate(js_id))

    auth2.check_super_admin_or_same_team(user_info, jobstate['team_id'])

    values['etag'] = utils.gen_etag()
    query = models.JOBSTATES.update().where(
        sqlalchemy.sql.and_(
            models.JOBSTATES.c.id == js_id,
            models.JOBSTATES.c.etag == if_match_etag)).values(**values)

    result = flask.g.db_conn.execute(query)

    if result.rowcount == 0:
        raise dci_exc.DCIException("Conflict on test '%s' or etag "
                                   "not matched." % js_id, status_code=409)

    return flask.Response(None, 204, headers={'ETag': values['etag']},
                          content_type='application/json')


@api.route('/jobstates', methods=['GET'])
@auth2.requires_auth()
def get_all_jobstates(user_info, j_id=None):
    """Get all jobstates.
    """
    args = schemas.args(flask.request.args.to_dict())
    embed = args['embed']

    v1_utils.verify_embed_list(embed, _VALID_EMBED.keys())

    # the default query with no parameters
    query = sqlalchemy.sql.select([models.JOBSTATES])

    # if embed then construct the query with a join
    if embed:
        query = v1_utils.get_query_with_join(models.JOBSTATES,
                                             [models.JOBSTATES], embed,
                                             _VALID_EMBED)

    if user_info.role != auth2.SUPER_ADMIN:
        query = query.where(models.JOBSTATES.c.team_id == user_info.team)

    query = v1_utils.sort_query(query, args['sort'], _JS_COLUMNS)
    query = v1_utils.where_query(query, args['where'], models.JOBSTATES,
                                 _JS_COLUMNS)

    # used for counting the number of rows when j_id is not None
    where_j_cond = None
    if j_id is not None:
        where_j_cond = models.JOBSTATES.c.job_id == j_id
        query = query.where(where_j_cond)

    # adds the limit/offset parameters
    if args['limit'] is not None:
        query = query.limit(args['limit'])

    if args['offset'] is not None:
        query = query.offset(args['offset'])

    # get the number of rows for the '_meta' section
    nb_row = utils.get_number_of_rows(models.JOBSTATES)

    rows = flask.g.db_conn.execute(query).fetchall()
    result = [v1_utils.group_embedded_resources(embed, row) for row in rows]

    result = {'jobstates': result, '_meta': {'count': nb_row}}
    result = json.dumps(result, default=utils.json_encoder)
    return flask.Response(result, 200, content_type='application/json')


@api.route('/jobstates/<js_id>', methods=['GET'])
@auth2.requires_auth()
def get_jobstate_by_id(user_info, js_id):
    embed = schemas.args(flask.request.args.to_dict())['embed']
    v1_utils.verify_embed_list(embed, _VALID_EMBED.keys())

    # the default query with no parameters
    query = sqlalchemy.sql.select([models.JOBSTATES])

    # if embed then construct the query with a join
    if embed:
        query = v1_utils.get_query_with_join(models.JOBSTATES,
                                             [models.JOBSTATES], embed,
                                             _VALID_EMBED)

    if user_info.role != auth2.SUPER_ADMIN:
        query = query.where(models.JOBSTATES.c.team_id == user_info.team)

    query = query.where(models.JOBSTATES.c.id == js_id)

    row = flask.g.db_conn.execute(query).fetchone()
    jobstate = v1_utils.group_embedded_resources(embed, row)

    if row is None:
        raise dci_exc.DCIException("Jobstate '%s' not found." % js_id,
                                   status_code=404)

    etag = jobstate['etag']
    jobstate = json.dumps({'jobstate': jobstate}, default=utils.json_encoder)
    return flask.Response(jobstate, 200, headers={'ETag': etag},
                          content_type='application/json')


@api.route('/jobstates/<js_id>', methods=['DELETE'])
@auth2.requires_auth()
def delete_jobstate_by_id(user_info, js_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    jobstate = dict(_verify_existence_and_get_jobstate(js_id))

    auth2.check_super_admin_or_same_team(user_info, jobstate['team_id'])

    where_clause = sqlalchemy.sql.and_(
        models.JOBSTATES.c.id == js_id,
        models.JOBSTATES.c.etag == if_match_etag
    )
    query = models.JOBSTATES.delete().where(where_clause)

    result = flask.g.db_conn.execute(query)

    if result.rowcount == 0:
        raise dci_exc.DCIException("Jobstate '%s' already deleted or "
                                   "etag not matched." % js_id,
                                   status_code=409)

    return flask.Response(None, 204, content_type='application/json')
