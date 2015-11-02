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
from dci.server.common import exceptions
from dci.server.common import utils
from dci.server.db import models_core as models

from dci.server.api.v1 import components


def _verify_existence_and_get_ct(ct_id):
    return v1_utils.verify_existence_and_get(
        models.COMPONENTYPES, ct_id,
        sqlalchemy.sql.or_(models.COMPONENTYPES.c.id == ct_id,
                           models.COMPONENTYPES.c.name == ct_id))


@api.route('/componenttypes', methods=['POST'])
def create_componenttypes():
    data_json = flask.request.json
    # verif post
    etag = utils.gen_etag()
    values = {'id': utils.gen_uuid(),
              'name': data_json['name'],
              'created_at': datetime.datetime.utcnow(),
              'updated_at': datetime.datetime.utcnow(),
              'etag': etag}

    query = models.COMPONENTYPES.insert().values(**values)
    try:
        flask.g.db_conn.execute(query)
    except sa_exc.DBAPIError as e:
        raise exceptions.DCIException(str(e))

    # verif dump
    result = {'componenttype': values}
    result = json.dumps(result)
    return flask.Response(result, 201, headers={'ETag': etag},
                          content_type='application/json')


@api.route('/componenttypes', methods=['GET'])
def get_all_componenttypes():
    limit = flask.request.args.get('limit', 10)
    offset = flask.request.args.get('offset', 0)
    query = sqlalchemy.sql.select([models.COMPONENTYPES]).\
        limit(limit).offset(offset)
    nb_cts = utils.get_number_of_rows(models.COMPONENTYPES)

    try:
        rows = flask.g.db_conn.execute(query).fetchall()
        result = [dict(row) for row in rows]
    except sa_exc.DBAPIError as e:
        raise exceptions.DCIException(str(e), status_code=500)

    # verif dump
    result = {'componenttypes': result, '_meta': {'count': nb_cts}}
    result = json.dumps(result, default=utils.json_encoder)
    return flask.Response(result, 200, content_type='application/json')


@api.route('/componenttypes/<ct_id>', methods=['GET'])
def get_componenttype_by_id_or_name(ct_id):
    componenttype = _verify_existence_and_get_ct(ct_id)
    etag = componenttype['etag']
    # verif dump
    componenttype = {'componenttype': dict(componenttype)}
    componenttype = json.dumps(componenttype, default=utils.json_encoder)
    return flask.Response(componenttype, 200, headers={'ETag': etag},
                          content_type='application/json')


@api.route('/componenttypes/<ct_id>/components', methods=['GET'])
def get_components_by_componenttype(ct_id):
    componenttype = _verify_existence_and_get_ct(ct_id)
    return components.get_all_components(componenttype['id'])


@api.route('/componenttypes/<ct_id>', methods=['PUT'])
def put_componenttype(ct_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    data_json = flask.request.json
    # verif put

    _verify_existence_and_get_ct(ct_id)

    data_json['etag'] = utils.gen_etag()
    query = models.COMPONENTYPES.update().where(
        sqlalchemy.sql.and_(
            sqlalchemy.sql.or_(models.COMPONENTYPES.c.id == ct_id,
                               models.COMPONENTYPES.c.name == ct_id),
            models.COMPONENTYPES.c.etag == if_match_etag)).values(**data_json)

    try:
        result = flask.g.db_conn.execute(query)
    except sa_exc.DBAPIError as e:
        raise exceptions.DCIException(str(e))

    if result.rowcount == 0:
        raise exceptions.DCIException("Conflict on componenttype '%s' or etag "
                                      "not matched." % ct_id, status_code=409)

    return flask.Response(None, 204, headers={'ETag': data_json['etag']},
                          content_type='application/json')


@api.route('/componenttypes/<ct_id>', methods=['DELETE'])
def delete_componenttype_by_id_or_name(ct_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    _verify_existence_and_get_ct(ct_id)

    query = models.COMPONENTYPES.delete().where(
        sqlalchemy.sql.and_(
            sqlalchemy.sql.or_(models.COMPONENTYPES.c.id == ct_id,
                               models.COMPONENTYPES.c.name == ct_id),
            models.COMPONENTYPES.c.etag == if_match_etag))

    try:
        result = flask.g.db_conn.execute(query)
    except sa_exc.DBAPIError as e:
        raise exceptions.DCIException(str(e), status_code=500)

    if result.rowcount == 0:
        raise exceptions.DCIException("Componenttype '%s' already deleted or "
                                      "etag not matched." % ct_id,
                                      status_code=409)

    return flask.Response(None, 204, content_type='application/json')
