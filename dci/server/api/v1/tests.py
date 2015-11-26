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
from dci.server.api.v1 import jobdefinitions
from dci.server.api.v1 import utils as v1_utils
from dci.server import auth2
from dci.server.common import exceptions
from dci.server.common import schemas
from dci.server.common import utils
from dci.server.db import models_core as models


# associate column names with the corresponding SA Column object
_T_COLUMNS = v1_utils.get_columns_name_with_objects(models.TESTS)


def _verify_existence_and_get_t(t_id):
    return v1_utils.verify_existence_and_get(
        [models.TESTS], t_id,
        sqlalchemy.sql.or_(models.TESTS.c.id == t_id,
                           models.TESTS.c.name == t_id))


@api.route('/tests', methods=['POST'])
@auth2.requires_auth()
def create_tests(user_info):
    etag = utils.gen_etag()
    data_json = schemas.test.post(flask.request.json)
    data_json.update({
        'id': utils.gen_uuid(),
        'created_at': datetime.datetime.utcnow().isoformat(),
        'updated_at': datetime.datetime.utcnow().isoformat(),
        'etag': etag
    })

    query = models.TESTS.insert().values(**data_json)
    flask.g.db_conn.execute(query)

    return flask.Response(
        json.dumps({'test': data_json}), 201, headers={'ETag': etag},
        content_type='application/json'
    )


@api.route('/tests', methods=['GET'])
@auth2.requires_auth()
def get_all_tests(user_info):
    args = schemas.args(flask.request.args.to_dict())

    query = (sqlalchemy.sql.select([models.TESTS])
             .limit(args['limit']).offset(args['offset']))

    query = v1_utils.sort_query(query, args['sort'], _T_COLUMNS)
    query = v1_utils.where_query(query, args['where'], models.TESTS,
                                 _T_COLUMNS)

    nb_cts = utils.get_number_of_rows(models.TESTS)

    rows = flask.g.db_conn.execute(query).fetchall()
    result = [dict(row) for row in rows]

    # verif dump
    result = {'tests': result, '_meta': {'count': nb_cts}}
    result = json.dumps(result, default=utils.json_encoder)
    return flask.Response(result, 200, content_type='application/json')


@api.route('/tests/<t_id>', methods=['GET'])
@auth2.requires_auth()
def get_test_by_id_or_name(user_info, t_id):
    test = _verify_existence_and_get_t(t_id)
    etag = test['etag']
    test = {'test': dict(test)}
    test = json.dumps(test, default=utils.json_encoder)
    return flask.Response(test, 200, headers={'ETag': etag},
                          content_type='application/json')


@api.route('/tests/<t_id>/jobdefinitions', methods=['GET'])
@auth2.requires_auth()
def get_jobdefinitions_by_test(user_info, test_id):
    test = _verify_existence_and_get_t(test_id)
    return jobdefinitions.get_all_jobdefinitions(test['id'])


@api.route('/tests/<t_id>', methods=['PUT'])
@auth2.requires_auth()
def put_test(user_info, t_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    data_json = schemas.test.put(flask.request.json)

    _verify_existence_and_get_t(t_id)
    data_json['etag'] = utils.gen_etag()

    where_clause = sqlalchemy.sql.and_(
        sqlalchemy.sql.or_(models.TESTS.c.id == t_id,
                           models.TESTS.c.name == t_id),
        models.TESTS.c.etag == if_match_etag
    )
    query = models.TESTS.update().where(where_clause).values(**data_json)

    result = flask.g.db_conn.execute(query)

    if result.rowcount == 0:
        raise exceptions.DCIException("Conflict on test '%s' or etag "
                                      "not matched." % t_id, status_code=409)

    return flask.Response(None, 204, headers={'ETag': data_json['etag']},
                          content_type='application/json')


@api.route('/tests/<t_id>', methods=['DELETE'])
@auth2.requires_auth()
def delete_test_by_id_or_name(user_info, t_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    _verify_existence_and_get_t(t_id)

    where_clause = sqlalchemy.sql.and_(
        sqlalchemy.sql.or_(models.TESTS.c.id == t_id,
                           models.TESTS.c.name == t_id),
        models.TESTS.c.etag == if_match_etag
    )
    query = models.TESTS.delete().where(where_clause)
    result = flask.g.db_conn.execute(query)

    if result.rowcount == 0:
        raise exceptions.DCIException("Test '%s' already deleted or "
                                      "etag not matched." % t_id,
                                      status_code=409)

    return flask.Response(None, 204, content_type='application/json')
