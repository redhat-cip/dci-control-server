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

from dci import dci_config
from dci.api.v1 import api
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import models

# associate column names with the corresponding SA Column object
_TABLE = models.COMPONENTS
_JJC = models.JOIN_JOBS_COMPONENTS
_C_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)
_JOBS_C_COLUMNS = v1_utils.get_columns_name_with_objects(models.JOBS)

EMBED = {
    'jobs_components': v1_utils.embed(_JJC)
}


@api.route('/components', methods=['POST'])
@auth.requires_auth
def create_components(user):
    if not(auth.is_admin(user)):
        raise auth.UNAUTHORIZED

    values = schemas.component.post(flask.request.json)
    values.update({
        'id': utils.gen_uuid(),
        'created_at': datetime.datetime.utcnow().isoformat(),
    })

    query = _TABLE.insert().values(**values)

    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(_TABLE.name, 'name')

    result = json.dumps({'component': values})
    return flask.Response(result, 201, content_type='application/json')


@api.route('/components/<c_id>', methods=['PUT'])
@auth.requires_auth
def update_components(user, c_id):
    if not(auth.is_admin(user)):
        raise auth.UNAUTHORIZED

    values = schemas.component.post(flask.request.json)
    values.update({
        'id': c_id,
        'updated_at': datetime.datetime.utcnow().isoformat(),
    })

    query = _TABLE.update().values(**values)

    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(_TABLE.name, 'name')

    result = json.dumps({'component': values})
    return flask.Response(result, 201, content_type='application/json')


def get_all_components(user, topic_id):
    """Get all components of a topic."""
    # get the diverse parameters
    args = schemas.args(flask.request.args.to_dict())

    q_bd = v1_utils.QueryBuilder(_TABLE, args['offset'], args['limit'])

    q_bd.sort = v1_utils.sort_query(args['sort'], _C_COLUMNS)
    q_bd.where = v1_utils.where_query(args['where'], _TABLE, _C_COLUMNS)
    q_bd.where.append(_TABLE.c.topic_id == topic_id)

    nb_row = flask.g.db_conn.execute(q_bd.build_nb_row()).scalar()
    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()

    return flask.jsonify({'components': rows, '_meta': {'count': nb_row}})


def get_jobs(user, component_id, team_id=None):
    """Get all the jobs associated to a specific component. If team_id is
    provided then filter by the jobs by team_id otherwise returns all the
    jobs.
    """

    args = schemas.args(flask.request.args.to_dict())

    q_bd = v1_utils.QueryBuilder(models.JOBS, args['offset'], args['limit'],
                                 EMBED)
    q_bd.sort = v1_utils.sort_query(args['sort'], _JOBS_C_COLUMNS)

    q_bd.join(['jobs_components'])
    q_bd.ignore_columns(['configuration'])
    q_bd.where.append(_JJC.c.component_id == component_id)
    if team_id:
        q_bd.where.append(models.JOBS.c.team_id == team_id)

    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()
    return flask.jsonify({'jobs': rows, '_meta': {'count': len(rows)}})


@api.route('/components/<c_id>', methods=['GET'])
@auth.requires_auth
def get_component_by_id_or_name(user, c_id):
    where_clause = sql.or_(_TABLE.c.id == c_id,
                           _TABLE.c.name == c_id)

    query = sql.select([_TABLE]).where(where_clause)

    component = flask.g.db_conn.execute(query).fetchone()

    if component is None:
        raise dci_exc.DCINotFound('Component', c_id)

    v1_utils.verify_team_in_topic(user, component['topic_id'])

    res = flask.jsonify({'component': component})
    return res


@api.route('/components/<c_id>', methods=['DELETE'])
@auth.requires_auth
def delete_component_by_id_or_name(user, c_id):
    # get If-Match header
    if not(auth.is_admin(user)):
        raise auth.UNAUTHORIZED

    v1_utils.verify_existence_and_get(c_id, _TABLE)

    where_clause = sql.or_(_TABLE.c.id == c_id, _TABLE.c.name == c_id)

    query = _TABLE.delete().where(where_clause)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIDeleteConflict('Component', c_id)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/components/<c_id>/files', methods=['GET'])
@auth.requires_auth
def list_components_files(user, c_id):
    component = v1_utils.verify_existence_and_get(c_id, _TABLE)
    v1_utils.verify_team_in_topic(user, component['topic_id'])

    # Todo SQL list

    res = flask.jsonify({'component': 'todo'})
    return res


@api.route('/components/<c_id>/files/<f_id>', methods=['GET'])
@auth.requires_auth
def download_component_file(user, c_id, f_id):
    # Todo SQL Select

    # Todo Swift get
    store = dci_config.get_store()
    store.get('GET FILE %s' % c_id)
    
    res = flask.jsonify({'component': 'todo'})
    return res


@api.route('/components/<c_id>/files', methods=['POST'])
@auth.requires_auth
def upload_component_file(user, c_id):
    if not(auth.is_admin(user)):
        raise auth.UNAUTHORIZED
    # Todo Swift upload

    # Todo SQL Insert

    res = flask.jsonify({'component': 'todo'})
    return res


@api.route('/components/<c_id>/files/<f_id>', methods=['DELETE'])
@auth.requires_auth
def delete_component_file(user, c_id, f_id):
    # TODO Swift Delete

    # Todo SQL Delete

    res = flask.jsonify({'component': 'todo'})
    return res
