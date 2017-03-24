# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Red Hat, Inc
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
import flask
from flask import json
from sqlalchemy import exc as sa_exc
from sqlalchemy import sql

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import jobdefinitions
from dci.api.v1 import remotecis
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import embeds
from dci.db import models


_TABLE = models.TESTS
_VALID_EMBED = embeds.tests()
# associate column names with the corresponding SA Column object
_T_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)


@api.route('/tests', methods=['POST'])
@auth.requires_auth
def create_tests(user):
    created_at, _ = utils.get_dates(user)
    data_json = schemas.test.post(flask.request.json)
    data_json.update({
        'id': utils.gen_uuid(),
        'created_at': created_at,
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


@api.route('/tests/<uuid:t_id>', methods=['PUT'])
@auth.requires_auth
def update_tests(user, t_id):
    if not(auth.is_admin(user)):
        raise auth.UNAUTHORIZED

    v1_utils.verify_existence_and_get(t_id, _TABLE)
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    values = schemas.component.put(flask.request.json)
    values['etag'] = utils.gen_etag()

    where_clause = sql.and_(
        _TABLE.c.etag == if_match_etag,
        _TABLE.c.id == t_id
    )

    query = _TABLE.update().where(where_clause).values(**values)

    result = flask.g.db_conn.execute(query)
    if not result.rowcount:
        raise dci_exc.DCIConflict('Test', t_id)

    return flask.Response(None, 204, headers={'ETag': values['etag']},
                          content_type='application/json')


def get_all_tests(user, team_id):
    args = schemas.args(flask.request.args.to_dict())
    embed = args['embed']

    if not(auth.is_admin(user) or auth.is_in_team(user, team_id)):
        raise auth.UNAUTHORIZED

    q_bd = v1_utils.QueryBuilder(_TABLE, args['offset'], args['limit'],
                                 _VALID_EMBED)
    q_bd.join(embed)

    q_bd.sort = v1_utils.sort_query(args['sort'], _T_COLUMNS)
    q_bd.where = v1_utils.where_query(args['where'], _TABLE, _T_COLUMNS)
    q_bd.where.append(_TABLE.c.team_id == team_id)

    q_bd.where.append(_TABLE.c.state != 'archived')

    # get the number of rows for the '_meta' section
    nb_row = flask.g.db_conn.execute(q_bd.build_nb_row()).scalar()
    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()
    rows = q_bd.dedup_rows(rows)

    return flask.jsonify({'tests': rows, '_meta': {'count': nb_row}})


@api.route('/tests/<uuid:t_id>', methods=['GET'])
@auth.requires_auth
def get_test_by_id_or_name(user, t_id):
    test = v1_utils.verify_existence_and_get(t_id, _TABLE)
    if not(auth.is_admin(user) or auth.is_in_team(user, test['team_id'])):
        raise auth.UNAUTHORIZED
    res = flask.jsonify({'test': test})
    return res


@api.route('/tests/<uuid:t_id>/jobdefinitions', methods=['GET'])
@auth.requires_auth
def get_jobdefinitions_by_test(user, test_id):
    test = v1_utils.verify_existence_and_get(test_id, _TABLE)
    if not(auth.is_admin(user) or auth.is_in_team(user, test['team_id'])):
        raise auth.UNAUTHORIZED
    return jobdefinitions.get_all_jobdefinitions(test['id'])


@api.route('/tests/<uuid:t_id>/remotecis', methods=['GET'])
@auth.requires_auth
def get_remotecis_by_test(user, test_id):
    test = v1_utils.verify_existence_and_get(test_id, _TABLE)
    return remotecis.get_all_remotecis(test['id'])


@api.route('/tests/<uuid:t_id>', methods=['DELETE'])
@auth.requires_auth
def delete_test_by_id_or_name(user, t_id):
    test = v1_utils.verify_existence_and_get(t_id, _TABLE)

    if not(auth.is_admin(user) or auth.is_in_team(user, test['team_id'])):
        raise auth.UNAUTHORIZED

    values = {'state': 'archived'}
    where_clause = _TABLE.c.id == t_id
    query = _TABLE.update().where(where_clause).values(**values)
    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIDeleteConflict('Test', t_id)

    for model in [models.FILES]:
        query = model.update().where(model.c.test_id == t_id).values(**values)
        flask.g.db_conn.execute(query)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/tests/purge', methods=['GET'])
@auth.requires_auth
def get_to_purge_archived_tests(user):
    return base.get_to_purge_archived_resources(user, _TABLE)


@api.route('/tests/purge', methods=['POST'])
@auth.requires_auth
def purge_archived_tests(user):
    return base.purge_archived_resources(user, _TABLE)
