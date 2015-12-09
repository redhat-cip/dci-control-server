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
from dci.server import auth
from dci.server.common import exceptions
from dci.server.common import schemas
from dci.server.common import utils
from dci.server.db import models

from dci.server.api.v1 import components

# associate column names with the corresponding SA Column object
_CT_COLUMNS = v1_utils.get_columns_name_with_objects(models.COMPONENTYPES)


def _verify_existence_and_get_ct(ct_id):
    return v1_utils.verify_existence_and_get(
        [models.COMPONENTYPES], ct_id,
        sqlalchemy.sql.or_(models.COMPONENTYPES.c.id == ct_id,
                           models.COMPONENTYPES.c.name == ct_id))


@api.route('/componenttypes', methods=['POST'])
@auth.requires_auth()
def create_componenttypes(user_info):
    values = schemas.componenttype.post(flask.request.json)
    etag = utils.gen_etag()
    values.update({
        'id': utils.gen_uuid(),
        'created_at': datetime.datetime.utcnow().isoformat(),
        'updated_at': datetime.datetime.utcnow().isoformat(),
        'etag': etag
    })

    query = models.COMPONENTYPES.insert().values(**values)

    flask.g.db_conn.execute(query)

    return flask.Response(
        json.dumps({'componenttype': values}), 201,
        headers={'ETag': etag}, content_type='application/json'
    )


@api.route('/componenttypes', methods=['GET'])
@auth.requires_auth()
def get_all_componenttypes(user_info):
    args = schemas.args(flask.request.args.to_dict())

    query = sqlalchemy.sql.select([models.COMPONENTYPES])

    if args['limit'] is not None:
        query = query.limit(args['limit'])

    if args['offset'] is not None:
        query = query.offset(args['offset'])

    query = v1_utils.sort_query(query, args['sort'], _CT_COLUMNS)
    query = v1_utils.where_query(query, args['where'], models.COMPONENTYPES,
                                 _CT_COLUMNS)

    nb_cts = utils.get_number_of_rows(models.COMPONENTYPES)

    rows = flask.g.db_conn.execute(query).fetchall()
    result = [dict(row) for row in rows]

    # verif dump
    result = {'componenttypes': result, '_meta': {'count': nb_cts}}
    result = json.dumps(result, default=utils.json_encoder)
    return flask.Response(result, 200, content_type='application/json')


@api.route('/componenttypes/<ct_id>', methods=['GET'])
@auth.requires_auth()
def get_componenttype_by_id_or_name(user_info, ct_id):
    componenttype = _verify_existence_and_get_ct(ct_id)
    etag = componenttype['etag']
    # verif dump
    componenttype = {'componenttype': dict(componenttype)}
    componenttype = json.dumps(componenttype, default=utils.json_encoder)
    return flask.Response(componenttype, 200, headers={'ETag': etag},
                          content_type='application/json')


@api.route('/componenttypes/<ct_id>/components', methods=['GET'])
@auth.requires_auth()
def get_components_by_componenttype(user_info, ct_id):
    componenttype = _verify_existence_and_get_ct(ct_id)
    return components.get_all_components(componenttype['id'])


@api.route('/componenttypes/<ct_id>', methods=['PUT'])
@auth.requires_auth()
def put_componenttype(user_info, ct_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    data_json = schemas.componenttype.put(flask.request.json)

    _verify_existence_and_get_ct(ct_id)

    data_json['etag'] = utils.gen_etag()
    query = models.COMPONENTYPES.update().where(
        sqlalchemy.sql.and_(
            sqlalchemy.sql.or_(models.COMPONENTYPES.c.id == ct_id,
                               models.COMPONENTYPES.c.name == ct_id),
            models.COMPONENTYPES.c.etag == if_match_etag)).values(**data_json)

    result = flask.g.db_conn.execute(query)

    if result.rowcount == 0:
        raise exceptions.DCIException("Conflict on componenttype '%s' or etag "
                                      "not matched." % ct_id, status_code=409)

    return flask.Response(None, 204, headers={'ETag': data_json['etag']},
                          content_type='application/json')


@api.route('/componenttypes/<ct_id>', methods=['DELETE'])
@auth.requires_auth()
def delete_componenttype_by_id_or_name(user_info, ct_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    _verify_existence_and_get_ct(ct_id)

    query = models.COMPONENTYPES.delete().where(
        sqlalchemy.sql.and_(
            sqlalchemy.sql.or_(models.COMPONENTYPES.c.id == ct_id,
                               models.COMPONENTYPES.c.name == ct_id),
            models.COMPONENTYPES.c.etag == if_match_etag))

    result = flask.g.db_conn.execute(query)

    if result.rowcount == 0:
        raise exceptions.DCIException("Componenttype '%s' already deleted or "
                                      "etag not matched." % ct_id,
                                      status_code=409)

    return flask.Response(None, 204, content_type='application/json')
