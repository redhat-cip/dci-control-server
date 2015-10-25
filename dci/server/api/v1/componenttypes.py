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
import uuid

import flask
from flask import json
from sqlalchemy import exc as sa_exc
import sqlalchemy.sql

from dci.server.api.v1 import api
from dci.server.common import exceptions
from dci.server.db import models_core as models
from dci.server import utils


def _is_uuid(value):
    try:
        return uuid.UUID(value)
    except ValueError:
        return None


def _get_cmp_by_name_or_id(query, resource_id):
    resource_id_uuid = _is_uuid(resource_id)
    if resource_id_uuid:
        return query.where(models.COMPONENTYPES.c.id == resource_id_uuid)
    else:
        return query.where(models.COMPONENTYPES.c.name == resource_id)


@api.route('/componenttypes', methods=['POST'])
def create_componenttypes():
    form_dict = flask.request.form.to_dict()

    query = models.COMPONENTYPES.insert().values(**form_dict)
    try:
        result = flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise exceptions.DCIException(
            "Componenttype '%s' already exist." % form_dict['name'])
    except sa_exc.DBAPIError as e:
        raise exceptions.ServerError(str(e))
    result = {'id': str(result.inserted_primary_key[0])}
    result = json.dumps(result)
    return flask.Response(result, 201, content_type='application/json')


@api.route('/componenttypes', methods=['GET'])
def get_all_componenttypes():
    query = sqlalchemy.sql.select([models.COMPONENTYPES])
    try:
        rows = flask.g.db_conn.execute(query).fetchall()
        result = [dict(row) for row in rows]
    except sa_exc.DBAPIError as e:
        raise exceptions.DCIException(str(e), status_code=500)

    result = {'componenttypes': result}
    result = json.dumps(result, default=utils.json_encoder)
    return flask.Response(result, 200, content_type='application/json')


@api.route('/componenttypes/<ct_id>', methods=['GET'])
def get_componenttype_by_id_or_name(ct_id):
    query = sqlalchemy.sql.select([models.COMPONENTYPES])
    query = _get_cmp_by_name_or_id(query, ct_id)

    try:
        result = flask.g.db_conn.execute(query).fetchone()
    except sa_exc.DBAPIError as e:
        raise exceptions.ServerError(str(e))

    if result is None:
        raise exceptions.DCIException("Component type '%s' not found." % ct_id,
                                      status_code=404)

    result = dict(result)
    result = json.dumps(result, default=utils.json_encoder)
    return flask.Response(result, 200, content_type='application/json')


@api.route('/componenttypes/<ct_id>', methods=['DELETE'])
def delete_componenttype_by_id_or_name(ct_id):
    query = sqlalchemy.sql.select([models.COMPONENTYPES])
    query = _get_cmp_by_name_or_id(query, ct_id)
    try:
        result = flask.g.db_conn.execute(query).fetchone()
    except sa_exc.DBAPIError as e:
        raise exceptions.DCIException(str(e), status_code=500)

    if result is None:
        raise exceptions.DCIException("Component type '%s' not found." % ct_id,
                                      status_code=404)

    query = models.COMPONENTYPES.delete()
    query = _get_cmp_by_name_or_id(query, ct_id)

    try:
        result = flask.g.db_conn.execute(query)
    except sa_exc.DBAPIError as e:
        raise exceptions.DCIException(str(e), status_code=500)

    if result.rowcount == 0:
        raise exceptions.DCIException("Conflict on component type '%s'." %
                                      ct_id, status_code=409)

    return flask.Response(None, 204, content_type='application/json')
