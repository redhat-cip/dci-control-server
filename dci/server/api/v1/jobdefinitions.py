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
from dci.server.common import exceptions as dci_exc
from dci.server.common import schemas
from dci.server.common import utils
from dci.server.db import models_core as models

# associate column names with the corresponding SA Column object
_JD_COLUMNS = v1_utils.get_columns_name_with_objects(models.JOBDEFINITIONS)
_VALID_EMBED = {'test': models.TESTS}


def _verify_existence_and_get_jd(jd_id):
    return v1_utils.verify_existence_and_get(
        models.JOBDEFINITIONS, jd_id,
        sqlalchemy.sql.or_(models.JOBDEFINITIONS.c.id == jd_id,
                           models.JOBDEFINITIONS.c.name == jd_id))


@api.route('/jobdefinitions', methods=['POST'])
def create_jobdefinitions():
    data_json = flask.request.json
    # verif post
    etag = utils.gen_etag()
    values = {'id': utils.gen_uuid(),
              'created_at': datetime.datetime.utcnow().isoformat(),
              'updated_at': datetime.datetime.utcnow().isoformat(),
              'etag': etag,
              'name': data_json['name'],
              'priority': data_json.get('priority', 0),
              'test_id': data_json.get('test_id', None)}

    query = models.JOBDEFINITIONS.insert().values(**values)

    flask.g.db_conn.execute(query)

    # verif dump
    result = {'jobdefinition': values}
    result = json.dumps(result)
    return flask.Response(result, 201, headers={'ETag': etag},
                          content_type='application/json')


@api.route('/jobdefinitions', methods=['GET'])
def get_all_jobdefinitions(t_id=None):
    """Get all jobdefinitions.

    If t_id is not None, then return all the jobdefinitions with a test
    pointed by t_id.
    """
    # get the diverse parameters
    args = schemas.args(flask.request.args.to_dict())
    # convenient alias
    embed = args['embed']

    v1_utils.verify_embed_list(embed, _VALID_EMBED.keys())

    # the default query with no parameters
    query = sqlalchemy.sql.select([models.JOBDEFINITIONS])

    # if embed then construct the query with a join
    if embed:
        query = v1_utils.get_query_with_join(models.JOBDEFINITIONS, embed,
                                             _VALID_EMBED)

    query = v1_utils.sort_query(query, args['sort'], _JD_COLUMNS)
    query = v1_utils.where_query(query, args['where'], models.JOBDEFINITIONS,
                                 _JD_COLUMNS)

    # used for counting the number of rows when t_id is not None
    where_t_cond = None
    if t_id is not None:
        where_t_cond = models.JOBDEFINITIONS.c.test_id == t_id
        query = query.where(where_t_cond)

    # adds the limit/offset parameters
    query = query.limit(args['limit']).offset(args['offset'])

    # get the number of rows for the '_meta' section
    nb_row = utils.get_number_of_rows(models.JOBDEFINITIONS, where_t_cond)

    rows = flask.g.db_conn.execute(query).fetchall()
    result = [v1_utils.group_embedded_resources(embed, row) for row in rows]

    # verif dump
    result = {'jobdefinitions': result, '_meta': {'count': nb_row}}
    result = json.dumps(result, default=utils.json_encoder)
    return flask.Response(result, 200, content_type='application/json')


@api.route('/jobdefinitions/<jd_id>', methods=['GET'])
def get_jobdefinition_by_id_or_name(jd_id):
    # get the diverse parameters
    embed = schemas.args(flask.request.args.to_dict())['embed']
    v1_utils.verify_embed_list(embed, _VALID_EMBED.keys())

    # the default query with no parameters
    query = sqlalchemy.sql.select([models.JOBDEFINITIONS])

    # if embed then construct the query with a join
    if embed:
        query = v1_utils.get_query_with_join(models.JOBDEFINITIONS, embed,
                                             _VALID_EMBED)

    query = query.where(
        sqlalchemy.sql.or_(models.JOBDEFINITIONS.c.id == jd_id,
                           models.JOBDEFINITIONS.c.name == jd_id))

    row = flask.g.db_conn.execute(query).fetchone()
    jobdefinition = v1_utils.group_embedded_resources(embed, row)

    if row is None:
        raise dci_exc.DCIException("Jobdefinition '%s' not found." % jd_id,
                                   status_code=404)

    etag = jobdefinition['etag']
    # verif dump
    jobdefinition = {'jobdefinition': jobdefinition}
    jobdefinition = json.dumps(jobdefinition, default=utils.json_encoder)
    return flask.Response(jobdefinition, 200, headers={'ETag': etag},
                          content_type='application/json')


@api.route('/jobdefinitions/<jd_id>', methods=['DELETE'])
def delete_jobdefinition_by_id_or_name(jd_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    _verify_existence_and_get_jd(jd_id)

    query = models.JOBDEFINITIONS.delete().where(
        sqlalchemy.sql.and_(
            sqlalchemy.sql.or_(models.JOBDEFINITIONS.c.id == jd_id,
                               models.JOBDEFINITIONS.c.name == jd_id),
            models.JOBDEFINITIONS.c.etag == if_match_etag))

    result = flask.g.db_conn.execute(query)

    if result.rowcount == 0:
        raise dci_exc.DCIException("Jobdefinition '%s' already deleted or "
                                   "etag not matched." % jd_id,
                                   status_code=409)

    return flask.Response(None, 204, content_type='application/json')

# Controllers for jobdefinition and components management


@api.route('/jobdefinitions/<jd_id>/components', methods=['POST'])
def add_component_to_jobdefinitions(jd_id):
    data_json = flask.request.json
    # verif post
    values = {'jobdefinition_id': jd_id,
              'component_id': data_json.get('component_id', None)}

    _verify_existence_and_get_jd(jd_id)

    query = models.JOIN_JOBDEFINITIONS_COMPONENTS.insert().values(**values)
    flask.g.db_conn.execute(query)
    return flask.Response(None, 201, content_type='application/json')


@api.route('/jobdefinitions/<jd_id>/components', methods=['GET'])
def get_all_components_from_jobdefinitions(jd_id):
    _verify_existence_and_get_jd(jd_id)

    # Get all components which belongs to a given jobdefinition
    query = sqlalchemy.sql.select([models.COMPONENTS]).select_from(
        models.JOIN_JOBDEFINITIONS_COMPONENTS.join(models.COMPONENTS)).where(
        models.JOIN_JOBDEFINITIONS_COMPONENTS.c.jobdefinition_id == jd_id)

    rows = flask.g.db_conn.execute(query)
    result = [dict(row) for row in rows]
    result = {'components': result, '_meta': {'count': len(result)}}
    result = json.dumps(result, default=utils.json_encoder)
    return flask.Response(result, 201, content_type='application/json')


@api.route('/jobdefinitions/<jd_id>/components/<c_id>', methods=['DELETE'])
def delete_component_from_jobdefinition(jd_id, c_id):
    _verify_existence_and_get_jd(jd_id)

    JDC = models.JOIN_JOBDEFINITIONS_COMPONENTS
    query = JDC.delete().where(
        sqlalchemy.sql.and_(JDC.c.jobdefinition_id == jd_id,
                            JDC.c.component_id == c_id))
    result = flask.g.db_conn.execute(query)

    if result.rowcount == 0:
        raise dci_exc.DCIException("Component '%s' already deleted." % c_id,
                                   status_code=409)

    return flask.Response(None, 204, content_type='application/json')
