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
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import token
from dci.common import utils
from dci.db import embeds
from dci.db import models

# associate column names with the corresponding SA Column object
_TABLE = models.REMOTECIS
_VALID_EMBED = embeds.remotecis()
_R_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)
_EMBED_MANY = {
    'team': False,
    'lastjob': False,
    'lastjob.components': True,
    'currentjob': False,
    'currentjob.components': True
}


@api.route('/remotecis', methods=['POST'])
@auth.login_required
def create_remotecis(user):
    values = v1_utils.common_values_dict(user)
    values.update(schemas.remoteci.post(flask.request.json))

    # If it's not a super admin nor belongs to the same team_id
    if not(auth.is_admin(user) or
           auth.is_in_team(user, values.get('team_id'))):
        raise auth.UNAUTHORIZED

    values.update({
        'data': values.get('data', {}),
        # XXX(fc): this should be populated as a default value from the
        # model, but we don't return values from the database :(
        'api_secret': token.gen_token(),
    })

    query = _TABLE.insert().values(**values)

    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(_TABLE.name, 'name')

    return flask.Response(
        json.dumps({'remoteci': values}), 201,
        headers={'ETag': values['etag']}, content_type='application/json'
    )


@api.route('/remotecis', methods=['GET'])
@auth.login_required
def get_all_remotecis(user, t_id=None):
    args = schemas.args(flask.request.args.to_dict())

    # build the query thanks to the QueryBuilder class
    query = v1_utils.QueryBuilder2(_TABLE, args, _R_COLUMNS)

    # If it's not an admin then restrict the view to the team's file
    if not auth.is_admin(user):
        query.add_extra_condition(_TABLE.c.team_id == user['team_id'])

    if t_id is not None:
        query.add_extra_condition(_TABLE.c.team_id == t_id)

    query.add_extra_condition(_TABLE.c.state != 'archived')

    rows = query.execute(fetchall=True)
    rows = v1_utils.format_result(rows, _TABLE.name, args['embed'],
                                  _EMBED_MANY)

    return flask.jsonify({'remotecis': rows, '_meta': {'count': len(rows)}})


@api.route('/remotecis/<uuid:r_id>', methods=['GET'])
@auth.login_required
def get_remoteci_by_id(user, r_id):

    args = schemas.args(flask.request.args.to_dict())

    # build the query thanks to the QueryBuilder class
    query = v1_utils.QueryBuilder2(_TABLE, args, _R_COLUMNS)

    # If it's not an admin then restrict the view to the team's file
    if not auth.is_admin(user):
        query.add_extra_condition(_TABLE.c.team_id == user['team_id'])

    query.add_extra_condition(_TABLE.c.id == r_id)

    query.add_extra_condition(_TABLE.c.state != 'archived')

    nb_rows = query.get_number_of_rows()
    rows = query.execute(fetchall=True)
    rows = v1_utils.format_result(rows, _TABLE.name, args['embed'],
                                  _EMBED_MANY)
    if len(rows) != 1:
        raise dci_exc.DCINotFound('Remoteci', r_id)

    res = flask.jsonify({'remoteci': rows[0], '_meta': {'count': nb_rows}})
    res.headers.add_header('ETag', rows[0]['etag'])
    return res


@api.route('/remotecis/<uuid:r_id>', methods=['PUT'])
@auth.login_required
def put_remoteci(user, r_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    values = schemas.remoteci.put(flask.request.json)

    remoteci = v1_utils.verify_existence_and_get(r_id, _TABLE)

    if 'data' in values:
        remoteci_data = get_remoteci_data_json(user, r_id)
        remoteci_data.update(values['data'])
        values['data'] = {k: v for k, v in remoteci_data.items() if v}

    if not(auth.is_admin(user) or auth.is_in_team(user, remoteci['team_id'])):
        raise auth.UNAUTHORIZED

    values['etag'] = utils.gen_etag()
    where_clause = sql.and_(_TABLE.c.etag == if_match_etag,
                            _TABLE.c.state != 'archived',
                            _TABLE.c.id == r_id)

    query = (_TABLE
             .update()
             .where(where_clause)
             .values(**values))

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict('RemoteCI', r_id)

    return flask.Response(None, 204, headers={'ETag': values['etag']},
                          content_type='application/json')


@api.route('/remotecis/<uuid:remoteci_id>', methods=['DELETE'])
@auth.login_required
def delete_remoteci_by_id(user, remoteci_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    remoteci = v1_utils.verify_existence_and_get(remoteci_id, _TABLE)

    if not(auth.is_admin(user) or auth.is_in_team(user, remoteci['team_id'])):
        raise auth.UNAUTHORIZED

    with flask.g.db_conn.begin():
        values = {'state': 'archived'}
        where_clause = sql.and_(
            _TABLE.c.etag == if_match_etag,
            _TABLE.c.id == remoteci_id
        )
        query = _TABLE.update().where(where_clause).values(**values)

        result = flask.g.db_conn.execute(query)

        if not result.rowcount:
            raise dci_exc.DCIDeleteConflict('RemoteCI', remoteci_id)

        for model in [models.JOBS]:
            query = model.update().where(model.c.remoteci_id == remoteci_id) \
                         .values(**values)
            flask.g.db_conn.execute(query)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/remotecis/<uuid:r_id>/data', methods=['GET'])
@auth.login_required
def get_remoteci_data(user, r_id):
    remoteci_data = get_remoteci_data_json(user, r_id)

    if 'keys' in 'keys' in flask.request.args:
        keys = flask.request.args.get('keys').split(',')
        remoteci_data = {k: remoteci_data[k] for k in keys
                         if k in remoteci_data}

    return flask.jsonify(remoteci_data)


def get_remoteci_data_json(user, r_id):
    query = v1_utils.QueryBuilder2(_TABLE, {}, _R_COLUMNS)

    if not auth.is_admin(user):
        query.add_extra_condition(_TABLE.c.team_id == user['team_id'])

    query.add_extra_condition(_TABLE.c.id == r_id)
    row = query.execute(fetchone=True)

    if row is None:
        raise dci_exc.DCINotFound('RemoteCI', r_id)

    return row['remotecis_data']


@api.route('/remotecis/<uuid:r_id>/tests', methods=['POST'])
@auth.login_required
def add_test_to_remoteci(user, r_id):
    # FIXME(fc): can any authenticated user add tests to *any* remoteci ?
    data_json = flask.request.json
    values = {'remoteci_id': r_id,
              'test_id': data_json.get('test_id', None)}

    v1_utils.verify_existence_and_get(r_id, _TABLE)

    query = models.JOIN_REMOTECIS_TESTS.insert().values(**values)
    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(_TABLE.name,
                                          'remoteci_id, test_id')
    result = json.dumps(values)
    return flask.Response(result, 201, content_type='application/json')


@api.route('/remotecis/<uuid:r_id>/tests', methods=['GET'])
@auth.login_required
def get_all_tests_from_remotecis(user, r_id):
    # FIXME(fc): can any authenticated user list tests from *any* remoteci ?
    v1_utils.verify_existence_and_get(r_id, _TABLE)

    # Get all components which belongs to a given remoteci
    JDC = models.JOIN_REMOTECIS_TESTS
    query = (sql.select([models.TESTS])
             .select_from(JDC.join(models.TESTS))
             .where(JDC.c.remoteci_id == r_id))
    rows = flask.g.db_conn.execute(query)

    res = flask.jsonify({'tests': rows,
                         '_meta': {'count': rows.rowcount}})
    return res


@api.route('/remotecis/<uuid:r_id>/tests/<uuid:t_id>', methods=['DELETE'])
@auth.login_required
def delete_test_from_remoteci(user, r_id, t_id):
    v1_utils.verify_existence_and_get(r_id, _TABLE)

    JDC = models.JOIN_REMOTECIS_TESTS
    where_clause = sql.and_(JDC.c.remoteci_id == r_id,
                            JDC.c.test_id == t_id)
    query = JDC.delete().where(where_clause)
    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict('Test', t_id)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/remotecis/purge', methods=['GET'])
@auth.login_required
def get_to_purge_archived_remotecis(user):
    return base.get_to_purge_archived_resources(user, _TABLE)


@api.route('/remotecis/purge', methods=['POST'])
@auth.login_required
def purge_archived_remotecis(user):
    return base.purge_archived_resources(user, _TABLE)


@api.route('/remotecis/<r_id>/api_secret', methods=['PUT'])
@auth.login_required
def put_api_secret(user, r_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    remoteci = v1_utils.verify_existence_and_get(r_id, _TABLE)

    if not(auth.is_admin(user) or auth.is_in_team(user, remoteci['team_id'])):
        raise auth.UNAUTHORIZED

    where_clause = sql.and_(
        _TABLE.c.etag == if_match_etag,
        sql.or_(_TABLE.c.id == r_id, _TABLE.c.name == r_id)
    )
    values = {
        'api_secret': token.gen_token(),
        'etag': utils.gen_etag()
    }

    query = (_TABLE
             .update()
             .where(where_clause)
             .values(**values))

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict('RemoteCI', r_id)

    res = flask.jsonify(({'id': r_id, 'etag': values['etag'],
                          'api_secret': values['api_secret']}))
    res.headers.add_header('ETag', values['etag'])
    return res
