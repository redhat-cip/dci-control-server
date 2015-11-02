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
from sqlalchemy import exc as sa_exc
import sqlalchemy.sql

from dci.server.api.v1 import api
from dci.server.api.v1 import v1_utils
from dci.server.common import exceptions as dci_exc
from dci.server.common import utils
from dci.server.db import models_core as models


_VALID_EMBED = {'componenttype': models.COMPONENTYPES}


def _verify_existence_and_get_c(c_id):
    return v1_utils.verify_existence_and_get(
        models.COMPONENTS, c_id,
        sqlalchemy.sql.or_(models.COMPONENTS.c.id == c_id,
                           models.COMPONENTS.c.name == c_id))


@api.route('/components', methods=['POST'])
def create_components():
    data_json = flask.request.json
    # verif post
    etag = utils.gen_etag()
    values = {'id': utils.gen_uuid(),
              'created_at': datetime.datetime.utcnow(),
              'updated_at': datetime.datetime.utcnow(),
              'etag': etag,
              'name': data_json['name'],
              'canonical_project_name': data_json.get(
                  'canonical_project_name', None),
              'data': data_json.get('data', None),
              'sha': data_json.get('sha', None),
              'title': data_json.get('title', None),
              'message': data_json.get('message', None),
              'url': data_json.get('url', None),
              'git': data_json.get('git', None),
              'ref': data_json.get('ref', None),
              'componenttype_id': data_json.get('componenttype_id', None)}

    query = models.COMPONENTS.insert().values(**values)
    try:
        flask.g.db_conn.execute(query)
    except sa_exc.DBAPIError as e:
        raise dci_exc.DCIException(str(e))

    # verif dump
    result = {'component': values}
    result = json.dumps(result)
    return flask.Response(result, 201, headers={'ETag': etag},
                          content_type='application/json')


@api.route('/components', methods=['GET'])
def get_all_components(ct_id=None):
    """Get all components.

    If ct_id is not None, then return all the components with a type
    pointed by ct_id.
    """
    # get the diverse parameters
    limit = flask.request.args.get('limit', 10)
    offset = flask.request.args.get('offset', 0)
    embed = flask.request.args.get('embed', '')
    embed_list = v1_utils.verify_embed_and_get_list(embed, _VALID_EMBED.keys())

    # the default query with no parameters
    query = sqlalchemy.sql.select([models.COMPONENTS])

    # if embed then construct the query with a join
    if embed_list:
        resources_to_embed = (_VALID_EMBED[elem] for elem in embed_list)
        query = v1_utils.get_query_with_join(models.COMPONENTS,
                                             *resources_to_embed)

    # used for counting the number of rows when ct_id is not None
    where_ct_cond = None
    if ct_id is not None:
        where_ct_cond = models.COMPONENTS.c.componenttype_id == ct_id
        query = query.where(where_ct_cond)

    # adds the limit/offset parameters
    query = query.limit(limit).offset(offset)

    # get the number of rows for the '_meta' section
    nb_cts = utils.get_number_of_rows(models.COMPONENTS, where_ct_cond)

    try:
        rows = flask.g.db_conn.execute(query).fetchall()
        result = [v1_utils.group_embedded_resources(embed_list, row)
                  for row in rows]
    except sa_exc.DBAPIError as e:
        raise dci_exc.DCIException(str(e), status_code=500)

    # verif dump
    result = {'components': result, '_meta': {'count': nb_cts}}
    result = json.dumps(result, default=utils.json_encoder)
    return flask.Response(result, 200, content_type='application/json')


@api.route('/components/<c_id>', methods=['GET'])
def get_component_by_id_or_name(c_id):
    # get the diverse parameters
    embed = flask.request.args.get('embed', '')
    embed_list = v1_utils.verify_embed_and_get_list(embed, _VALID_EMBED.keys())

    # the default query with no parameters
    query = sqlalchemy.sql.select([models.COMPONENTS])

    # if embed then construct the query with a join
    if embed_list:
        resources_to_embed = (_VALID_EMBED[elem] for elem in embed_list)
        query = v1_utils.get_query_with_join(models.COMPONENTS,
                                             *resources_to_embed)

    query = query.where(sqlalchemy.sql.or_(models.COMPONENTS.c.id == c_id,
                                           models.COMPONENTS.c.name == c_id))

    try:
        row = flask.g.db_conn.execute(query).fetchone()
        component = v1_utils.group_embedded_resources(embed_list, row)
    except sa_exc.DBAPIError as e:
        raise dci_exc.DCIException(str(e), status_code=500)

    if row is None:
        raise dci_exc.DCIException("component '%s' not found." % c_id,
                                   status_code=404)

    etag = component['etag']
    # verif dump
    component = {'component': component}
    component = json.dumps(component, default=utils.json_encoder)
    return flask.Response(component, 200, headers={'ETag': etag},
                          content_type='application/json')


@api.route('/components/<c_id>', methods=['DELETE'])
def delete_component_by_id_or_name(c_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    _verify_existence_and_get_c(c_id)

    query = models.COMPONENTS.delete().where(
        sqlalchemy.sql.and_(
            sqlalchemy.sql.or_(models.COMPONENTS.c.id == c_id,
                               models.COMPONENTS.c.name == c_id),
            models.COMPONENTS.c.etag == if_match_etag))

    try:
        result = flask.g.db_conn.execute(query)
    except sa_exc.DBAPIError as e:
        raise dci_exc.DCIException(str(e), status_code=500)

    if result.rowcount == 0:
        raise dci_exc.DCIException("Component '%s' already deleted or "
                                   "etag not matched." % c_id,
                                   status_code=409)

    return flask.Response(None, 204, content_type='application/json')
