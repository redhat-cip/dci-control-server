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
from dci.server.common import exceptions
from dci.server.common import utils
from dci.server.db import models_core as models


def _get_component_verify_existence(c_id):
    query = sqlalchemy.sql.select([models.COMPONENTS]).where(
        sqlalchemy.sql.or_(models.COMPONENTS.c.id == c_id,
                           models.COMPONENTS.c.name == c_id))

    try:
        result = flask.g.db_conn.execute(query).fetchone()
    except sa_exc.DBAPIError as e:
        raise exceptions.DCIException(str(e), status_code=500)

    if result is None:
        raise exceptions.DCIException("Component '%s' not found." % c_id,
                                      status_code=404)
    return result


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
        raise exceptions.DCIException(str(e))

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
    limit = flask.request.args.get('limit', 10)
    offset = flask.request.args.get('offset', 0)
    query = sqlalchemy.sql.select([models.COMPONENTS])
    if ct_id is not None:
        query = query.where(models.COMPONENTS.c.componenttype_id == ct_id)
    query = query.limit(limit).offset(offset)

    nb_cts = utils.get_number_of_rows(models.COMPONENTS)

    try:
        rows = flask.g.db_conn.execute(query).fetchall()
        result = [dict(row) for row in rows]
    except sa_exc.DBAPIError as e:
        raise exceptions.DCIException(str(e), status_code=500)

    # verif dump
    result = {'components': result, '_meta': {'count': nb_cts}}
    result = json.dumps(result, default=utils.json_encoder)
    return flask.Response(result, 200, content_type='application/json')


@api.route('/components/<c_id>', methods=['GET'])
def get_component_by_id_or_name(c_id):
    component = _get_component_verify_existence(c_id)
    etag = component['etag']
    # verif dump
    component = {'component': dict(component)}
    component = json.dumps(component, default=utils.json_encoder)
    return flask.Response(component, 200, headers={'ETag': etag},
                          content_type='application/json')


@api.route('/components/<c_id>', methods=['DELETE'])
def delete_component_by_id_or_name(c_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    _get_component_verify_existence(c_id)

    query = models.COMPONENTS.delete().where(
        sqlalchemy.sql.and_(
            sqlalchemy.sql.or_(models.COMPONENTS.c.id == c_id,
                               models.COMPONENTS.c.name == c_id),
            models.COMPONENTS.c.etag == if_match_etag))

    try:
        result = flask.g.db_conn.execute(query)
    except sa_exc.DBAPIError as e:
        raise exceptions.DCIException(str(e), status_code=500)

    if result.rowcount == 0:
        raise exceptions.DCIException("Component '%s' already deleted or "
                                      "etag not matched." % c_id,
                                      status_code=409)

    return flask.Response(None, 204, content_type='application/json')
