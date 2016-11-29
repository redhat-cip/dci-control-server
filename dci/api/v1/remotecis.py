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
import uuid
from flask import json
from sqlalchemy import exc as sa_exc
from sqlalchemy import sql

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import embeds
from dci.db import models

# associate column names with the corresponding SA Column object
_TABLE = models.REMOTECIS
_VALID_EMBED = embeds.remotecis()
_R_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)


@api.route('/remotecis', methods=['POST'])
@auth.requires_auth({auth.AUTH_BASIC})
def create_remotecis(user):
    created_at, updated_at = utils.get_dates(user)
    values = schemas.remoteci.post(flask.request.json)

    # If it's not a super admin nor belongs to the same team_id
    if not(auth.is_admin(user) or
           auth.is_in_team(user, values.get('team_id'))):
        raise auth.UNAUTHORIZED

    etag = utils.gen_etag()
    values.update({
        'id': utils.gen_uuid(),
        'api_secret': utils.gen_secret(),
        'created_at': created_at,
        'updated_at': updated_at,
        'data': values.get('data', {}),
        'etag': etag
    })

    query = _TABLE.insert().values(**values)

    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(_TABLE.name, 'name')

    return flask.Response(
        json.dumps({'remoteci': values}), 201,
        headers={'ETag': etag}, content_type='application/json'
    )


@api.route('/remotecis', methods=['GET'])
@auth.requires_auth({auth.AUTH_BASIC})
def get_all_remotecis(user, t_id=None):
    args = schemas.args(flask.request.args.to_dict())
    embed = args['embed']

    q_bd = v1_utils.QueryBuilder(_TABLE, args['offset'], args['limit'],
                                 _VALID_EMBED)
    q_bd.join(embed)
    q_bd.sort = v1_utils.sort_query(args['sort'], _R_COLUMNS, default='name')
    q_bd.where = v1_utils.where_query(args['where'], _TABLE, _R_COLUMNS)

    # If it's not an admin then restrict the view to the team's file
    if not auth.is_admin(user):
        q_bd.where.append(_TABLE.c.team_id == user['team_id'])

    if t_id is not None:
        q_bd.where.append(_TABLE.c.team_id == t_id)

    q_bd.where.append(_TABLE.c.state != 'archived')

    nb_row = flask.g.db_conn.execute(q_bd.build_nb_row()).scalar()
    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()
    rows = q_bd.dedup_rows(rows)

    return flask.jsonify({'remotecis': rows, '_meta': {'count': nb_row}})


@api.route('/remotecis/<r_id>', methods=['GET'])
@auth.requires_auth({auth.AUTH_BASIC})
def get_remoteci_by_id_or_name(user, r_id):
    embed = schemas.args(flask.request.args.to_dict())['embed']

    q_bd = v1_utils.QueryBuilder(_TABLE, embed=_VALID_EMBED)
    q_bd.join(embed)

    if not auth.is_admin(user):
        q_bd.where.append(_TABLE.c.team_id == user['team_id'])

    try:
        uuid.UUID(r_id)
        q_bd.where.append(
            sql.and_(
                _TABLE.c.state != 'archived',
                _TABLE.c.id == r_id
            )
        )
    except ValueError:
        q_bd.where.append(
            sql.and_(
                _TABLE.c.state != 'archived',
                _TABLE.c.name == r_id
            )
        )

    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()
    rows = q_bd.dedup_rows(rows)
    if len(rows) != 1:
        raise dci_exc.DCINotFound('RemoteCI', r_id)
    remoteci = rows[0]

    res = flask.jsonify({'remoteci': remoteci})
    res.headers.add_header('ETag', remoteci['etag'])
    return res


@api.route('/remotecis/<r_id>', methods=['PUT'])
@auth.requires_auth({auth.AUTH_BASIC})
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


@api.route('/remotecis/<r_id>', methods=['DELETE'])
@auth.requires_auth({auth.AUTH_BASIC})
def delete_remoteci_by_id_or_name(user, r_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    remoteci = v1_utils.verify_existence_and_get(r_id, _TABLE)

    if not(auth.is_admin(user) or auth.is_in_team(user, remoteci['team_id'])):
        raise auth.UNAUTHORIZED

    values = {'state': 'archived'}
    where_clause = sql.and_(
        _TABLE.c.etag == if_match_etag,
        _TABLE.c.id == r_id
    )
    query = _TABLE.update().where(where_clause).values(**values)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIDeleteConflict('RemoteCI', r_id)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/remotecis/<r_id>/data', methods=['GET'])
@auth.requires_auth({auth.AUTH_BASIC})
def get_remoteci_data(user, r_id):
    remoteci_data = get_remoteci_data_json(user, r_id)

    if 'keys' in 'keys' in flask.request.args:
        keys = flask.request.args.get('keys').split(',')
        remoteci_data = {k: remoteci_data[k] for k in keys
                         if k in remoteci_data}

    return flask.jsonify(remoteci_data)


def get_remoteci_data_json(user, r_id):
    q_bd = v1_utils.QueryBuilder(_TABLE)

    if not auth.is_admin(user):
        q_bd.where.append(_TABLE.c.team_id == user['team_id'])

    q_bd.where.append(sql.or_(_TABLE.c.id == r_id, _TABLE.c.name == r_id))
    row = flask.g.db_conn.execute(q_bd.build()).fetchone()

    if row is None:
        raise dci_exc.DCINotFound('RemoteCI', r_id)

    return row['remotecis_data']


@api.route('/remotecis/<r_id>/tests', methods=['POST'])
@auth.requires_auth({auth.AUTH_BASIC})
def add_test_to_remoteci(user, r_id):
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


@api.route('/remotecis/<r_id>/tests', methods=['GET'])
@auth.requires_auth({auth.AUTH_BASIC})
def get_all_tests_from_remotecis(user, r_id):
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


@api.route('/remotecis/<r_id>/tests/<t_id>', methods=['DELETE'])
@auth.requires_auth({auth.AUTH_BASIC})
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
@auth.requires_auth({auth.AUTH_BASIC})
def get_to_purge_archived_remotecis(user):
    return base.get_to_purge_archived_resources(user, _TABLE)


@api.route('/remotecis/purge', methods=['POST'])
@auth.requires_auth({auth.AUTH_BASIC})
def purge_archived_remotecis(user):
    return base.purge_archived_resources(user, _TABLE)


@api.route('/remotecis/<r_id>/api_secret', methods=['PUT'])
@auth.requires_auth({auth.AUTH_BASIC})
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
        'api_secret': utils.gen_secret(),
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
