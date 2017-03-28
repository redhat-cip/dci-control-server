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
from dci.api.v1 import tests
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci.common import audits
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import embeds
from dci.db import models

# associate column names with the corresponding SA Column object
_TABLE = models.TEAMS
_VALID_EMBED = embeds.teams()
_T_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)


@api.route('/teams', methods=['POST'])
@auth.requires_auth
@auth.requires_platform_admin
@audits.log
def create_teams(user):
    values = v1_utils.common_values_dict(user)
    values.update(schemas.team.post(flask.request.json))

    query = _TABLE.insert().values(**values)

    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(_TABLE.name, 'name')

    return flask.Response(
        json.dumps({'team': values}), 201,
        headers={'ETag': values['etag']}, content_type='application/json'
    )


@api.route('/teams', methods=['GET'])
@auth.requires_auth
def get_all_teams(user):
    args = schemas.args(flask.request.args.to_dict())
    embed = schemas.args(flask.request.args.to_dict())['embed']

    q_bd = v1_utils.QueryBuilder(_TABLE, args['offset'], args['limit'],
                                 embed=_VALID_EMBED)
    q_bd.join(embed)

    q_bd.sort = v1_utils.sort_query(args['sort'], _T_COLUMNS, default='name')
    q_bd.where = v1_utils.where_query(args['where'], _TABLE, _T_COLUMNS)

    if not auth.is_admin(user):
        q_bd.where.append(_TABLE.c.id == user['team_id'])

    q_bd.where.append(_TABLE.c.state != 'archived')

    nb_row = flask.g.db_conn.execute(q_bd.build_nb_row()).scalar()
    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()
    rows = q_bd.dedup_rows(rows)

    return flask.jsonify({'teams': rows, '_meta': {'count': nb_row}})


@api.route('/teams/<uuid:t_id>', methods=['GET'])
@auth.requires_auth
def get_team_by_id_or_name(user, t_id):
    embed = schemas.args(flask.request.args.to_dict())['embed']

    q_bd = v1_utils.QueryBuilder(_TABLE, embed=_VALID_EMBED)
    q_bd.join(embed)

    q_bd.where.append(
        sql.and_(
            _TABLE.c.state != 'archived',
            _TABLE.c.id == t_id
        )
    )

    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()
    rows = q_bd.dedup_rows(rows)
    if len(rows) != 1:
        raise dci_exc.DCINotFound('Team', t_id)
    team = rows[0]

    if not(auth.is_admin(user) or auth.is_in_team(user, team['id'])):
        raise auth.UNAUTHORIZED

    res = flask.jsonify({'team': team})
    res.headers.add_header('ETag', team['etag'])
    return res


@api.route('/teams/<uuid:team_id>/remotecis', methods=['GET'])
@auth.requires_auth
def get_remotecis_by_team(user, team_id):
    team = v1_utils.verify_existence_and_get(team_id, _TABLE)
    return remotecis.get_all_remotecis(team['id'])


@api.route('/teams/<uuid:team_id>/tests', methods=['GET'])
@auth.requires_auth
def get_tests_by_team(user, team_id):
    team = v1_utils.verify_existence_and_get(team_id, _TABLE)
    return tests.get_all_tests(user, team['id'])


@api.route('/teams/<uuid:t_id>', methods=['PUT'])
@auth.requires_auth
@auth.requires_team_admin
def put_team(user, t_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    values = schemas.team.put(flask.request.json)

    v1_utils.verify_existence_and_get(t_id, _TABLE)

    values['etag'] = utils.gen_etag()
    where_clause = sql.and_(
        _TABLE.c.etag == if_match_etag,
        _TABLE.c.id == t_id
    )
    query = _TABLE.update().where(where_clause).values(**values)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict('Team', t_id)

    return flask.Response(None, 204, headers={'ETag': values['etag']},
                          content_type='application/json')


@api.route('/teams/<uuid:t_id>', methods=['DELETE'])
@auth.requires_auth
@auth.requires_platform_admin
def delete_team_by_id_or_name(user, t_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    v1_utils.verify_existence_and_get(t_id, _TABLE)

    values = {'state': 'archived'}
    where_clause = sql.and_(
        _TABLE.c.etag == if_match_etag,
        _TABLE.c.id == t_id
    )
    query = _TABLE.update().where(where_clause).values(**values)
    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIDeleteConflict('Team', t_id)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/teams/purge', methods=['GET'])
@auth.requires_auth
@auth.requires_platform_admin
def get_to_purge_archived_teams(user):
    return base.get_to_purge_archived_resources(user, _TABLE)


@api.route('/teams/purge', methods=['POST'])
@auth.requires_auth
@auth.requires_platform_admin
def purge_archived_teams(user):
    return base.purge_archived_resources(user, _TABLE)
