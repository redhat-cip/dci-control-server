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

import datetime

import flask
from flask import json
from sqlalchemy import exc as sa_exc
from sqlalchemy import sql

from dci.api.v1 import api
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import models

from sqlalchemy.sql import and_
from sqlalchemy.sql import or_

# associate column names with the corresponding SA Column object
_TABLE = models.REMOTECIS
_R_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)
lj = models.JOBS.alias('last_job')
cj = models.JOBS.alias('current_job')
lj_components = models.COMPONENTS.alias('last_job.components')
cj_components = models.COMPONENTS.alias('current_job.components')
cjc = models.JOIN_JOBS_COMPONENTS.alias('cjc')
ljc = models.JOIN_JOBS_COMPONENTS.alias('ljc')
rci0 = models.REMOTECIS.alias('remoteci_0')
rci1 = models.REMOTECIS.alias('remoteci_1')
rci2 = models.REMOTECIS.alias('remoteci_2')
rci3 = models.REMOTECIS.alias('remoteci_3')
rci4 = models.REMOTECIS.alias('remoteci_4')
lj_t = models.JOBS.alias('last_job_t')
cj_t = models.JOBS.alias('current_job_t')
team = models.TEAMS.alias('team')

_VALID_EMBED = {
    'team': v1_utils.embed(
        select=[team],
        join=rci0.join(team, team.c.id == rci0.c.team_id),
        where=rci0.c.id == _TABLE.c.id),
    'last_job': v1_utils.embed(
        select=[lj],
        join=rci1.join(
            lj,
            and_(
                lj.c.remoteci_id == rci1.c.id,
                lj.c.status.in_([
                    'success',
                    'failure',
                    'killed',
                    'product-failure',
                    'deployment-failure'])),
            isouter=True),
        where=rci1.c.id == _TABLE.c.id,
        sort=lj.c.created_at),
    'last_job.components': v1_utils.embed(
        select=[lj_components],
        join=rci2.join(
            lj_t.join(
                ljc.join(
                    lj_components,
                    ljc.c.component_id == lj_components.c.id,
                    isouter=True),
                ljc.c.job_id == lj_t.c.id,
                isouter=True),
            lj_t.c.remoteci_id == rci2.c.id,
            isouter=True),
        where=and_(
            rci2.c.id == _TABLE.c.id,
            or_(
                lj.c.id == lj_t.c.id,
                lj.c.id == None)),
        many=True),
    'current_job': v1_utils.embed(
        select=[cj],
        join=rci3.join(
            cj,
            and_(
                cj.c.remoteci_id == rci3.c.id,
                cj.c.status.in_([
                    'new',
                    'pre-run',
                    'running'])),
            isouter=True),
        where=rci3.c.id == _TABLE.c.id,
        sort=cj.c.created_at),
    'current_job.components': v1_utils.embed(
        select=[cj_components],
        join=rci4.join(
            cj_t.join(
                cjc.join(
                    cj_components,
                    cjc.c.component_id == cj_components.c.id,
                    isouter=True),
                cjc.c.job_id == cj_t.c.id,
                isouter=True),
            cj_t.c.remoteci_id == rci4.c.id,
            isouter=True),
        where=and_(
            rci4.c.id == _TABLE.c.id,
            or_(
                cj.c.id == cj_t.c.id,
                cj.c.id == None)),  # noqa
        many=True)}


@api.route('/remotecis', methods=['POST'])
@auth.requires_auth
def create_remotecis(user):
    values = schemas.remoteci.post(flask.request.json)

    # If it's not a super admin nor belongs to the same team_id
    if not(auth.is_admin(user) or
           auth.is_in_team(user, values.get('team_id'))):
        raise auth.UNAUTHORIZED

    etag = utils.gen_etag()
    values.update({
        'id': utils.gen_uuid(),
        'created_at': datetime.datetime.utcnow().isoformat(),
        'updated_at': datetime.datetime.utcnow().isoformat(),
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
@auth.requires_auth
def get_all_remotecis(user, t_id=None):
    args = schemas.args(flask.request.args.to_dict())
    embed = args['embed']

    q_bd = v1_utils.QueryBuilder(_TABLE, args['offset'], args['limit'],
                                 _VALID_EMBED)
    q_bd.join(embed)
    q_bd.sort = v1_utils.sort_query(args['sort'], _R_COLUMNS)
    q_bd.where = v1_utils.where_query(args['where'], _TABLE, _R_COLUMNS)

    # If it's not an admin then restrict the view to the team's file
    if not auth.is_admin(user):
        q_bd.where.append(_TABLE.c.team_id == user['team_id'])

    if t_id is not None:
        q_bd.where.append(_TABLE.c.team_id == t_id)

    nb_row = flask.g.db_conn.execute(q_bd.build_nb_row()).scalar()
    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()
    rows = q_bd.dedup_rows(embed, rows)

    return flask.jsonify({'remotecis': rows, '_meta': {'count': nb_row}})


@api.route('/remotecis/<r_id>', methods=['GET'])
@auth.requires_auth
def get_remoteci_by_id_or_name(user, r_id):
    embed = schemas.args(flask.request.args.to_dict())['embed']

    q_bd = v1_utils.QueryBuilder(_TABLE, embed=_VALID_EMBED)
    q_bd.join(embed)

    if not auth.is_admin(user):
        q_bd.where.append(_TABLE.c.team_id == user['team_id'])

    q_bd.where.append(sql.or_(_TABLE.c.id == r_id, _TABLE.c.name == r_id))

    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()
    rows = q_bd.dedup_rows(embed, rows)
    if len(rows) != 1:
        raise dci_exc.DCINotFound('RemoteCI', r_id)
    remoteci = rows[0]

    res = flask.jsonify({'remoteci': remoteci})
    res.headers.add_header('ETag', remoteci['etag'])
    return res


@api.route('/remotecis/<r_id>', methods=['PUT'])
@auth.requires_auth
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
    where_clause = sql.and_(
        _TABLE.c.etag == if_match_etag,
        sql.or_(_TABLE.c.id == r_id, _TABLE.c.name == r_id)
    )

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
@auth.requires_auth
def delete_remoteci_by_id_or_name(user, r_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    remoteci = v1_utils.verify_existence_and_get(r_id, _TABLE)

    if not(auth.is_admin(user) or auth.is_in_team(user, remoteci['team_id'])):
        raise auth.UNAUTHORIZED

    where_clause = sql.and_(
        _TABLE.c.etag == if_match_etag,
        sql.or_(_TABLE.c.id == r_id, _TABLE.c.name == r_id)
    )
    query = _TABLE.delete().where(where_clause)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIDeleteConflict('RemoteCI', r_id)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/remotecis/<r_id>/data', methods=['GET'])
@auth.requires_auth
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
@auth.requires_auth
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
@auth.requires_auth
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
@auth.requires_auth
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
