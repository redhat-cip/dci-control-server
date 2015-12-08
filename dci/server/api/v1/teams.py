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
from dci.server.api.v1 import remotecis
from dci.server.api.v1 import utils as v1_utils
from dci.server import auth2
from dci.server.common import exceptions
from dci.server.common import schemas
from dci.server.common import utils
from dci.server.db import models_core as models

# associate column names with the corresponding SA Column object
_T_COLUMNS = v1_utils.get_columns_name_with_objects(models.TEAMS)


def _verify_existence_and_get_team(t_id):
    return v1_utils.verify_existence_and_get(
        [models.TEAMS], t_id,
        sqlalchemy.sql.or_(models.TEAMS.c.id == t_id,
                           models.TEAMS.c.name == t_id))


@api.route('/teams', methods=['POST'])
@auth2.requires_auth
def create_teams(user):
    values = schemas.team.post(flask.request.json)

    if not auth2.is_admin(user):
        raise auth2.UNAUTHORIZED

    etag = utils.gen_etag()
    values.update({
        'id': utils.gen_uuid(),
        'created_at': datetime.datetime.utcnow().isoformat(),
        'updated_at': datetime.datetime.utcnow().isoformat(),
        'etag': etag
    })

    query = models.TEAMS.insert().values(**values)

    flask.g.db_conn.execute(query)

    return flask.Response(
        json.dumps({'team': values}), 201,
        headers={'ETag': etag}, content_type='application/json'
    )


@api.route('/teams', methods=['GET'])
@auth2.requires_auth
def get_all_teams(user):
    args = schemas.args(flask.request.args.to_dict())

    query = sqlalchemy.sql.select([models.TEAMS])

    if args['limit'] is not None:
        query = query.limit(args['limit'])

    if args['offset'] is not None:
        query = query.offset(args['offset'])

    if not auth2.is_admin(user):
        query = query.where(models.TEAMS.c.id == user['team_id'])

    query = v1_utils.sort_query(query, args['sort'], _T_COLUMNS)
    query = v1_utils.where_query(query, args['where'], models.TEAMS,
                                 _T_COLUMNS)

    nb_cts = utils.get_number_of_rows(models.TEAMS)

    rows = flask.g.db_conn.execute(query).fetchall()
    result = [dict(row) for row in rows]

    result = {'teams': result, '_meta': {'count': nb_cts}}
    result = json.dumps(result, default=utils.json_encoder)
    return flask.Response(result, 200, content_type='application/json')


@api.route('/teams/<t_id>', methods=['GET'])
@auth2.requires_auth
def get_team_by_id_or_name(user, t_id):
    where_clause = sqlalchemy.sql.or_(models.TEAMS.c.id == t_id,
                                      models.TEAMS.c.name == t_id)
    query = (sqlalchemy.sql
             .select([models.TEAMS])
             .where(where_clause))

    team = flask.g.db_conn.execute(query).fetchone()
    if team is None:
        raise exceptions.DCIException("Team '%s' not found." % t_id,
                                      status_code=404)
    team = dict(team)
    auth2.is_admin_or_in_same_team(user, team['id'])

    etag = team['etag']
    team = json.dumps({'team': team}, default=utils.json_encoder)
    return flask.Response(team, 200, headers={'ETag': etag},
                          content_type='application/json')


@api.route('/teams/<team_id>/remotecis', methods=['GET'])
@auth2.requires_auth
def get_remotecis_by_team(user, team_id):
    team = _verify_existence_and_get_team(team_id)
    return remotecis.get_all_remotecis(team['id'])


@api.route('/teams/<t_id>', methods=['PUT'])
@auth2.requires_auth
def put_team(user, t_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    values = schemas.team.put(flask.request.json)

    auth2.is_admin_or_admin_user_in_same_team(user, t_id)

    _verify_existence_and_get_team(t_id)

    values['etag'] = utils.gen_etag()
    query = models.TEAMS.update().where(
        sqlalchemy.sql.and_(
            sqlalchemy.sql.or_(models.TEAMS.c.id == t_id,
                               models.TEAMS.c.name == t_id),
            models.TEAMS.c.etag == if_match_etag)).values(**values)

    result = flask.g.db_conn.execute(query)

    if result.rowcount == 0:
        raise exceptions.DCIException("Conflict on team '%s' or etag "
                                      "not matched." % t_id, status_code=409)

    return flask.Response(None, 204, headers={'ETag': values['etag']},
                          content_type='application/json')


@api.route('/teams/<ct_id>', methods=['DELETE'])
@auth2.requires_auth
def delete_team_by_id_or_name(user, ct_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    if not auth2.is_admin(user):
        raise auth2.UNAUTHORIZED

    _verify_existence_and_get_team(ct_id)

    where_clause = sqlalchemy.sql.and_(
        models.TEAMS.c.etag == if_match_etag,
        sqlalchemy.sql.or_(models.TEAMS.c.id == ct_id,
                           models.TEAMS.c.name == ct_id)
    )
    query = models.TEAMS.delete().where(where_clause)
    result = flask.g.db_conn.execute(query)

    if result.rowcount == 0:
        raise exceptions.DCIException("Team '%s' already deleted or "
                                      "etag not matched." % ct_id,
                                      status_code=409)

    return flask.Response(None, 204, content_type='application/json')
