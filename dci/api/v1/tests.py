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
from sqlalchemy import sql

from dci.api.v1 import api
from dci.api.v1 import jobdefinitions
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import models


_TABLE = models.TESTS
# associate column names with the corresponding SA Column object
_T_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)


@api.route('/tests', methods=['POST'])
@auth.requires_auth
def create_tests(user):
    data_json = schemas.test.post(flask.request.json)
    data_json.update({
        'id': utils.gen_uuid(),
        'created_at': datetime.datetime.utcnow().isoformat(),
    })

    query = _TABLE.insert().values(**data_json)
    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(_TABLE.name, 'name')

    return flask.Response(
        json.dumps({'test': data_json}), 201,
        content_type='application/json'
    )


@api.route('/tests', methods=['GET'])
@auth.requires_auth
def get_all_tests(user):
    args = schemas.args(flask.request.args.to_dict())

    q_bd = v1_utils.QueryBuilder(_TABLE, args['offset'], args['limit'])

    q_bd.sort = v1_utils.sort_query(args['sort'], _T_COLUMNS)
    q_bd.where = v1_utils.where_query(args['where'], _TABLE, _T_COLUMNS)

    # get the number of rows for the '_meta' section
    nb_row = flask.g.db_conn.execute(q_bd.build_nb_row()).scalar()
    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()

    return flask.jsonify({'tests': rows, '_meta': {'count': nb_row}})


@api.route('/tests/<t_id>', methods=['GET'])
@auth.requires_auth
def get_test_by_id_or_name(user, t_id):
    test = v1_utils.verify_existence_and_get(t_id, _TABLE)
    res = flask.jsonify({'test': test})
    return res


@api.route('/tests/<t_id>/jobdefinitions', methods=['GET'])
@auth.requires_auth
def get_jobdefinitions_by_test(user, test_id):
    test = v1_utils.verify_existence_and_get(test_id, _TABLE)
    return jobdefinitions.get_all_jobdefinitions(test['id'])


@api.route('/tests/<t_id>', methods=['DELETE'])
@auth.requires_auth
def delete_test_by_id_or_name(user, t_id):

    v1_utils.verify_existence_and_get(t_id, _TABLE)

    where_clause = sql.or_(_TABLE.c.id == t_id, _TABLE.c.name == t_id)
    query = _TABLE.delete().where(where_clause)
    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIDeleteConflict('Test', t_id)

    return flask.Response(None, 204, content_type='application/json')
