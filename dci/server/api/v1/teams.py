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

from dci.server.api.v1 import api
from dci.server.api.v1 import remotecis
from dci.server.api.v1 import utils as v1_utils
from dci.server import auth
from dci.server.common import exceptions as dci_exc
from dci.server.common import schemas
from dci.server.common import utils
from dci.server.db import models

# associate column names with the corresponding SA Column object
_TABLE = models.TEAMS
_T_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)


@api.route('/teams', methods=['POST'])
@auth.requires_auth
def create_teams(user):
    values = schemas.team.post(flask.request.json)

    if not auth.is_admin(user):
        raise auth.UNAUTHORIZED

    etag = utils.gen_etag()
    values.update({
        'id': utils.gen_uuid(),
        'created_at': datetime.datetime.utcnow().isoformat(),
        'updated_at': datetime.datetime.utcnow().isoformat(),
        'etag': etag
    })

    query = _TABLE.insert().values(**values)

    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(_TABLE.name, 'name')

    return flask.Response(
        json.dumps({'team': values}), 201,
        headers={'ETag': etag}, content_type='application/json'
    )


@api.route('/teams', methods=['GET'])
@auth.requires_auth
def get_all_teams(user):
    args = schemas.args(flask.request.args.to_dict())

    q_bd = v1_utils.QueryBuilder(_TABLE, args['offset'], args['limit'])

    q_bd.sort = v1_utils.sort_query(args['sort'], _T_COLUMNS)
    q_bd.where = v1_utils.where_query(args['where'], _TABLE, _T_COLUMNS)

    if not auth.is_admin(user):
        q_bd.where.append(_TABLE.c.id == user['team_id'])

    nb_row = flask.g.db_conn.execute(q_bd.build_nb_row()).scalar()
    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()

    return flask.jsonify({'teams': rows, '_meta': {'count': nb_row}})


@api.route('/teams/<t_id>', methods=['GET'])
@auth.requires_auth
def get_team_by_id_or_name(user, t_id):
    where_clause = sql.or_(_TABLE.c.id == t_id, _TABLE.c.name == t_id)

    query = sql.select([_TABLE]).where(where_clause)
    team = flask.g.db_conn.execute(query).fetchone()

    if team is None:
        raise dci_exc.DCINotFound('Team', t_id)
    if not(auth.is_admin(user) or auth.is_in_team(user, team['id'])):
        raise auth.UNAUTHORIZED

    res = flask.jsonify({'team': team})
    res.headers.add_header('ETag', team['etag'])
    return res


@api.route('/teams/<team_id>/remotecis', methods=['GET'])
@auth.requires_auth
def get_remotecis_by_team(user, team_id):
    team = v1_utils.verify_existence_and_get(team_id, _TABLE)
    return remotecis.get_all_remotecis(team['id'])


@api.route('/teams/<t_id>', methods=['PUT'])
@auth.requires_auth
def put_team(user, t_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    values = schemas.team.put(flask.request.json)

    if not(auth.is_admin(user) or auth.is_admin_user(user, t_id)):
        raise auth.UNAUTHORIZED

    v1_utils.verify_existence_and_get(t_id, _TABLE)

    values['etag'] = utils.gen_etag()
    where_clause = sql.and_(
        _TABLE.c.etag == if_match_etag,
        sql.or_(_TABLE.c.id == t_id, _TABLE.c.name == t_id)
    )
    query = _TABLE.update().where(where_clause).values(**values)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict('Team', t_id)

    return flask.Response(None, 204, headers={'ETag': values['etag']},
                          content_type='application/json')


@api.route('/teams/<t_id>', methods=['DELETE'])
@auth.requires_auth
def delete_team_by_id_or_name(user, t_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    if not auth.is_admin(user):
        raise auth.UNAUTHORIZED

    v1_utils.verify_existence_and_get(t_id, _TABLE)

    where_clause = sql.and_(
        _TABLE.c.etag == if_match_etag,
        sql.or_(_TABLE.c.id == t_id, _TABLE.c.name == t_id)
    )
    query = _TABLE.delete().where(where_clause)
    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIDeleteConflict('Team', t_id)

    return flask.Response(None, 204, content_type='application/json')
