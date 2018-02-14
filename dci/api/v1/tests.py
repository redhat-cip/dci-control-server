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
from dci.api.v1 import remotecis
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import embeds
from dci.db import models


_TABLE = models.TESTS
_VALID_EMBED = embeds.tests()
# associate column names with the corresponding SA Column object
_T_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)
_EMBED_MANY = {
    'topics': True
}


@api.route('/tests', methods=['POST'])
@decorators.login_required
@decorators.check_roles
def create_tests(user):
    values = v1_utils.common_values_dict(user)
    values.update(schemas.test.post(flask.request.json))

    query = _TABLE.insert().values(**values)

    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(_TABLE.name, 'name')

    return flask.Response(
        json.dumps({'test': values}), 201,
        content_type='application/json'
    )


@api.route('/tests/<uuid:t_id>', methods=['PUT'])
@decorators.login_required
@decorators.check_roles
def update_tests(user, t_id):
    v1_utils.verify_existence_and_get(t_id, _TABLE)
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    values = schemas.test.put(flask.request.json)
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

    query = v1_utils.QueryBuilder(_TABLE, args, _T_COLUMNS)
    if not user.is_super_admin():
        query.add_extra_condition(_TABLE.c.team_id.in_(user.teams))
    query.add_extra_condition(_TABLE.c.state != 'archived')

    # get the number of rows for the '_meta' section
    nb_rows = query.get_number_of_rows()
    rows = query.execute(fetchall=True)
    rows = v1_utils.format_result(rows, _TABLE.name, args['embed'],
                                  _EMBED_MANY)

    return flask.jsonify({'tests': rows, '_meta': {'count': nb_rows}})


@api.route('/tests/<uuid:t_id>', methods=['GET'])
@decorators.login_required
@decorators.check_roles
def get_test_by_id(user, t_id):
    test = v1_utils.verify_existence_and_get(t_id, _TABLE)
    if not user.is_in_team(test['team_id']) and not user.is_read_only_user():
        raise auth.UNAUTHORIZED
    res = flask.jsonify({'test': test})
    return res


@api.route('/tests/<uuid:t_id>/remotecis', methods=['GET'])
@decorators.login_required
@decorators.check_roles
def get_remotecis_by_test(user, test_id):
    test = v1_utils.verify_existence_and_get(test_id, _TABLE)
    return remotecis.get_all_remotecis(test['id'])


@api.route('/tests/<uuid:t_id>', methods=['DELETE'])
@decorators.login_required
@decorators.check_roles
def delete_test_by_id(user, t_id):
    test = v1_utils.verify_existence_and_get(t_id, _TABLE)

    if not user.is_in_team(test['team_id']):
        raise auth.UNAUTHORIZED

    with flask.g.db_conn.begin():
        values = {'state': 'archived'}
        where_clause = _TABLE.c.id == t_id
        query = _TABLE.update().where(where_clause).values(**values)
        result = flask.g.db_conn.execute(query)

        if not result.rowcount:
            raise dci_exc.DCIDeleteConflict('Test', t_id)

        for model in [models.FILES]:
            query = model.update().where(model.c.test_id == t_id).values(
                **values
            )
            flask.g.db_conn.execute(query)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/tests/purge', methods=['GET'])
@decorators.login_required
@decorators.check_roles
def get_to_purge_archived_tests(user):
    return base.get_to_purge_archived_resources(user, _TABLE)


@api.route('/tests/purge', methods=['POST'])
@decorators.login_required
@decorators.check_roles
def purge_archived_tests(user):
    return base.purge_archived_resources(user, _TABLE)
