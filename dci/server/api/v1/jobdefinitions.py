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
    limit = flask.request.args.get('limit', 20)
    offset = flask.request.args.get('offset', 0)
    embed_list = flask.request.args.get('embed', '').split(',')
    sort = flask.request.args.get('sort', '')
    where = flask.request.args.get('where', '')

    v1_utils.verify_embed_list(embed_list, _VALID_EMBED.keys())

    # the default query with no parameters
    query = sqlalchemy.sql.select([models.JOBDEFINITIONS])

    # if embed then construct the query with a join
    if embed_list != ['']:
        resources_to_embed = (_VALID_EMBED[elem] for elem in embed_list)
        query = v1_utils.get_query_with_join(models.JOBDEFINITIONS,
                                             *resources_to_embed)

    if sort:
        query = v1_utils.sort_query(query, sort, _JD_COLUMNS)

    if where:
        query = v1_utils.where_query(query, where, models.JOBDEFINITIONS,
                                     _JD_COLUMNS)

    # used for counting the number of rows when t_id is not None
    where_t_cond = None
    if t_id is not None:
        where_t_cond = models.JOBDEFINITIONS.c.test_id == t_id
        query = query.where(where_t_cond)

    # adds the limit/offset parameters
    query = query.limit(limit).offset(offset)

    # get the number of rows for the '_meta' section
    nb_row = utils.get_number_of_rows(models.JOBDEFINITIONS, where_t_cond)

    rows = flask.g.db_conn.execute(query).fetchall()
    result = [v1_utils.group_embedded_resources(embed_list, row)
              for row in rows]

    # verif dump
    result = {'jobdefinitions': result, '_meta': {'count': nb_row}}
    result = json.dumps(result, default=utils.json_encoder)
    return flask.Response(result, 200, content_type='application/json')


@api.route('/jobdefinitions/<jd_id>', methods=['GET'])
def get_jobdefinition_by_id_or_name(jd_id):
    # get the diverse parameters
    embed_list = flask.request.args.get('embed', '').split(',')
    v1_utils.verify_embed_list(embed_list, _VALID_EMBED.keys())

    # the default query with no parameters
    query = sqlalchemy.sql.select([models.JOBDEFINITIONS])

    # if embed then construct the query with a join
    if embed_list != ['']:
        resources_to_embed = (_VALID_EMBED[elem] for elem in embed_list)
        query = v1_utils.get_query_with_join(models.JOBDEFINITIONS,
                                             *resources_to_embed)

    query = query.where(
        sqlalchemy.sql.or_(models.JOBDEFINITIONS.c.id == jd_id,
                           models.JOBDEFINITIONS.c.name == jd_id))

    row = flask.g.db_conn.execute(query).fetchone()
    jobdefinition = v1_utils.group_embedded_resources(embed_list, row)

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
