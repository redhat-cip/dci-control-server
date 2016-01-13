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
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import models


# associate column names with the corresponding SA Column object
_TABLE = models.REMOTECIS
_R_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)
_VALID_EMBED = {'team': models.TEAMS}


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

    v1_utils.verify_embed_list(embed, _VALID_EMBED.keys())

    q_bd = v1_utils.QueryBuilder(_TABLE, args['offset'], args['limit'])

    select, join = v1_utils.get_query_with_join(embed, _VALID_EMBED)

    q_bd.select.extend(select)
    q_bd.join.extend(join)
    q_bd.sort = v1_utils.sort_query(args['sort'], _R_COLUMNS)
    q_bd.where = v1_utils.where_query(args['where'], _TABLE, _R_COLUMNS)

    # If it's not an admin then restrict the view to the team's file
    if not auth.is_admin(user):
        q_bd.where.append(_TABLE.c.team_id == user['team_id'])

    if t_id is not None:
        q_bd.where.append(_TABLE.c.team_id == t_id)

    nb_row = flask.g.db_conn.execute(q_bd.build_nb_row()).scalar()
    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()
    rows = [v1_utils.group_embedded_resources(embed, row) for row in rows]

    return flask.jsonify({'remotecis': rows, '_meta': {'count': nb_row}})


@api.route('/remotecis/<r_id>', methods=['GET'])
@auth.requires_auth
def get_remoteci_by_id_or_name(user, r_id):
    embed = schemas.args(flask.request.args.to_dict())['embed']
    v1_utils.verify_embed_list(embed, _VALID_EMBED.keys())

    q_bd = v1_utils.QueryBuilder(_TABLE)

    select, join = v1_utils.get_query_with_join(embed, _VALID_EMBED)
    q_bd.select.extend(select)
    q_bd.join.extend(join)

    if not auth.is_admin(user):
        q_bd.where.append(_TABLE.c.team_id == user['team_id'])

    q_bd.where.append(sql.or_(_TABLE.c.id == r_id, _TABLE.c.name == r_id))

    row = flask.g.db_conn.execute(q_bd.build()).fetchone()

    if row is None:
        raise dci_exc.DCINotFound('RemoteCI', r_id)

    remoteci = v1_utils.group_embedded_resources(embed, row)
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
