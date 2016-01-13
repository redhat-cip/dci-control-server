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
from sqlalchemy import sql

from dci.api.v1 import api
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import models

# associate column names with the corresponding SA Column object
_TABLE = models.JOBSTATES
_JS_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)
_VALID_EMBED = {'job': models.JOBS,
                'team': models.TEAMS}


@api.route('/jobstates', methods=['POST'])
@auth.requires_auth
def create_jobstates(user):
    values = schemas.jobstate.post(flask.request.json)

    # If it's not a super admin nor belongs to the same team_id
    if not(auth.is_admin(user) or auth.is_in_team(user, values['team_id'])):
        raise auth.UNAUTHORIZED

    etag = utils.gen_etag()
    values.update({
        'id': utils.gen_uuid(),
        'created_at': datetime.datetime.utcnow().isoformat(),
        'updated_at': datetime.datetime.utcnow().isoformat(),
        'etag': etag
    })

    query = _TABLE.insert().values(**values)

    flask.g.db_conn.execute(query)

    # Update job status
    job_id = values.get('job_id')

    query_update_job = (models.JOBS.update()
                        .where(models.JOBS.c.id == job_id)
                        .values(status=values.get('status')))

    result = flask.g.db_conn.execute(query_update_job)

    if not result.rowcount:
        raise dci_exc.DCIConflict('Job', job_id)

    result = json.dumps({'jobstate': values})
    return flask.Response(result, 201, headers={'ETag': etag},
                          content_type='application/json')


@api.route('/jobstates', methods=['GET'])
@auth.requires_auth
def get_all_jobstates(user, j_id=None):
    """Get all jobstates.
    """
    args = schemas.args(flask.request.args.to_dict())
    embed = args['embed']

    v1_utils.verify_embed_list(embed, _VALID_EMBED.keys())

    q_bd = v1_utils.QueryBuilder(_TABLE,
                                 args['limit'], args['offset'])

    select, join = v1_utils.get_query_with_join(embed, _VALID_EMBED)

    q_bd.select.extend(select)
    q_bd.join.extend(join)

    q_bd.sort = v1_utils.sort_query(args['sort'], _JS_COLUMNS)
    q_bd.where = v1_utils.where_query(args['where'], _TABLE, _JS_COLUMNS)

    if not auth.is_admin(user):
        q_bd.where.append(_TABLE.c.team_id == user['team_id'])

    # used for counting the number of rows when j_id is not None
    if j_id is not None:
        q_bd.where.append(_TABLE.c.job_id == j_id)

    # get the number of rows for the '_meta' section
    nb_row = flask.g.db_conn.execute(q_bd.build_nb_row()).scalar()
    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()

    rows = [v1_utils.group_embedded_resources(embed, row) for row in rows]

    return flask.jsonify({'jobstates': rows, '_meta': {'count': nb_row}})


@api.route('/jobstates/<js_id>', methods=['GET'])
@auth.requires_auth
def get_jobstate_by_id(user, js_id):
    embed = schemas.args(flask.request.args.to_dict())['embed']
    v1_utils.verify_embed_list(embed, _VALID_EMBED.keys())

    q_bd = v1_utils.QueryBuilder(_TABLE)

    select, join = v1_utils.get_query_with_join(embed, _VALID_EMBED)

    q_bd.select.extend(select)
    q_bd.join.extend(join)

    if not auth.is_admin(user):
        q_bd.where.append(_TABLE.c.team_id == user['team_id'])

    q_bd.where.append(_TABLE.c.id == js_id)

    row = flask.g.db_conn.execute(q_bd.build()).fetchone()

    if row is None:
        raise dci_exc.DCINotFound('Jobstate', js_id)

    jobstate = v1_utils.group_embedded_resources(embed, row)
    res = flask.jsonify({'jobstate': jobstate})
    res.headers.add_header('ETag', jobstate['etag'])
    return res


@api.route('/jobstates/<js_id>', methods=['DELETE'])
@auth.requires_auth
def delete_jobstate_by_id(user, js_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    jobstate = v1_utils.verify_existence_and_get(js_id, _TABLE)

    if not(auth.is_admin(user) or auth.is_in_team(user, jobstate['team_id'])):
        raise auth.UNAUTHORIZED

    where_clause = sql.and_(
        _TABLE.c.id == js_id,
        _TABLE.c.etag == if_match_etag
    )
    query = _TABLE.delete().where(where_clause)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIDeleteConflict('Jobstate', js_id)

    return flask.Response(None, 204, content_type='application/json')
