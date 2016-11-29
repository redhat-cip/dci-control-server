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
import uuid
from flask import json
from sqlalchemy import exc as sa_exc
from sqlalchemy import sql

from dci import dci_config
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
_TABLE = models.COMPONENTS
_JJC = models.JOIN_JOBS_COMPONENTS
_VALID_EMBED = embeds.components()
_C_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)
_JOBS_C_COLUMNS = v1_utils.get_columns_name_with_objects(models.JOBS)


@api.route('/components', methods=['POST'])
@auth.requires_auth({auth.AUTH_BASIC})
def create_components(user):
    created_at, updated_at = utils.get_dates(user)
    if not(auth.is_admin(user)):
        raise auth.UNAUTHORIZED

    values = schemas.component.post(flask.request.json)
    etag = utils.gen_etag()
    values.update({
        'id': utils.gen_uuid(),
        'created_at': created_at,
        'updated_at': updated_at,
        'etag': etag
    })

    query = _TABLE.insert().values(**values)

    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(_TABLE.name, 'name')

    result = json.dumps({'component': values})
    return flask.Response(result, 201, content_type='application/json')


@api.route('/components/<c_id>', methods=['PUT'])
@auth.requires_auth({auth.AUTH_BASIC})
def update_components(user, c_id):
    if not(auth.is_admin(user)):
        raise auth.UNAUTHORIZED

    v1_utils.verify_existence_and_get(c_id, _TABLE)
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    values = schemas.component.put(flask.request.json)
    values['etag'] = utils.gen_etag()

    where_clause = sql.and_(
        _TABLE.c.etag == if_match_etag,
        _TABLE.c.id == c_id
    )

    query = _TABLE.update().where(where_clause).values(**values)

    result = flask.g.db_conn.execute(query)
    if not result.rowcount:
        raise dci_exc.DCIConflict('Component', c_id)

    return flask.Response(None, 204, headers={'ETag': values['etag']},
                          content_type='application/json')


def get_all_components(user, topic_id):
    """Get all components of a topic."""
    # get the diverse parameters
    args = schemas.args(flask.request.args.to_dict())
    embed = args['embed']
    v1_utils.verify_team_in_topic(user, topic_id)

    q_bd = v1_utils.QueryBuilder(_TABLE, args['offset'], args['limit'],
                                 _VALID_EMBED)
    q_bd.join(embed)

    q_bd.sort = v1_utils.sort_query(args['sort'], _C_COLUMNS)
    q_bd.where = v1_utils.where_query(args['where'], _TABLE, _C_COLUMNS)
    where_clause = sql.and_(
        _TABLE.c.topic_id == topic_id,
        _TABLE.c.state != 'archived'
    )
    q_bd.where.append(where_clause)

    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()
    rows = q_bd.dedup_rows(rows)

    # Return only the component which have the export_control flag set to true
    #
    if not (auth.is_admin(user)):
        rows = [row for row in rows if row['export_control']]

    return flask.jsonify({'components': rows, '_meta': {'count': len(rows)}})


def get_jobs(user, component_id, team_id=None):
    """Get all the jobs associated to a specific component. If team_id is
    provided then filter by the jobs by team_id otherwise returns all the
    jobs.
    """
    args = schemas.args(flask.request.args.to_dict())
    embed = args['embed']

    q_bd = v1_utils.QueryBuilder(models.JOBS, args['offset'], args['limit'],
                                 _VALID_EMBED)
    q_bd.join(embed)
    q_bd.sort = v1_utils.sort_query(args['sort'], _JOBS_C_COLUMNS)

    q_bd.ignore_columns(['configuration'])
    q_bd.where.append(_JJC.c.component_id == component_id)
    if team_id:
        q_bd.where.append(models.JOBS.c.team_id == team_id)

    q_bd.where.append(models.JOBS.c.state != 'archived')

    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()
    rows = q_bd.dedup_rows(rows)
    return flask.jsonify({'jobs': rows, '_meta': {'count': len(rows)}})


@api.route('/components/<c_id>', methods=['GET'])
@auth.requires_auth({auth.AUTH_BASIC})
def get_component_by_id_or_name(user, c_id):
    embed = schemas.args(flask.request.args.to_dict())['embed']

    q_bd = v1_utils.QueryBuilder(_TABLE, embed=_VALID_EMBED)
    q_bd.join(embed)

    try:
        uuid.UUID(c_id)
        q_bd.where.append(
            sql.and_(
                _TABLE.c.state != 'archived',
                _TABLE.c.id == c_id
            )
        )
    except ValueError:
        q_bd.where.append(
            sql.and_(
                _TABLE.c.state != 'archived',
                _TABLE.c.name == c_id
            )
        )

    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()
    rows = q_bd.dedup_rows(rows)
    if len(rows) != 1:
        raise dci_exc.DCINotFound('Component', c_id)
    component = rows[0]
    auth.check_export_control(user, component)

    res = flask.jsonify({'component': component})
    return res


@api.route('/components/<c_id>', methods=['DELETE'])
@auth.requires_auth({auth.AUTH_BASIC})
def delete_component_by_id_or_name(user, c_id):
    # get If-Match header
    if not(auth.is_admin(user)):
        raise auth.UNAUTHORIZED

    try:
        uuid.UUID(c_id)
    except ValueError:
        raise dci_exc.DCIDeleteConflict('Component', c_id)

    v1_utils.verify_existence_and_get(c_id, _TABLE)

    values = {'state': 'archived'}
    where_clause = sql.and_(
        _TABLE.c.id == c_id
    )
    query = _TABLE.update().where(where_clause).values(**values)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIDeleteConflict('Component', c_id)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/components/purge', methods=['GET'])
@auth.requires_auth({auth.AUTH_BASIC})
def get_to_purge_archived_components(user):
    return base.get_to_purge_archived_resources(user, _TABLE)


@api.route('/components/purge', methods=['POST'])
@auth.requires_auth({auth.AUTH_BASIC})
def purge_archived_components(user):
    return base.purge_archived_resources(user, _TABLE)


@api.route('/components/<c_id>/files', methods=['GET'])
@auth.requires_auth({auth.AUTH_BASIC})
def list_components_files(user, c_id):
    component = v1_utils.verify_existence_and_get(c_id, _TABLE)
    v1_utils.verify_team_in_topic(user, component['topic_id'])

    args = schemas.args(flask.request.args.to_dict())

    COMPONENT_FILES = models.COMPONENT_FILES
    COLUMN_CF = v1_utils.get_columns_name_with_objects(COMPONENT_FILES)

    q_bd = v1_utils.QueryBuilder(COMPONENT_FILES,
                                 args['offset'], args['limit'],
                                 embed=_VALID_EMBED)

    q_bd.sort = v1_utils.sort_query(args['sort'], COLUMN_CF)
    q_bd.where = v1_utils.where_query(args['where'], COMPONENT_FILES,
                                      COLUMN_CF)
    q_bd.where.append(COMPONENT_FILES.c.component_id == c_id)

    nb_row = flask.g.db_conn.execute(q_bd.build_nb_row()).scalar()
    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()
    rows = q_bd.dedup_rows(rows)

    return flask.jsonify({'component_files': rows, '_meta': {'count': nb_row}})


@api.route('/components/<c_id>/files/<f_id>', methods=['GET'])
@auth.requires_auth({auth.AUTH_BASIC})
def list_component_file(user, c_id, f_id):
    component = v1_utils.verify_existence_and_get(c_id, _TABLE)
    auth.check_export_control(user, component)
    v1_utils.verify_team_in_topic(user, component['topic_id'])

    COMPONENT_FILES = models.COMPONENT_FILES
    where_clause = sql.and_(COMPONENT_FILES.c.id == f_id,
                            COMPONENT_FILES.c.component_id == c_id)

    query = sql.select([COMPONENT_FILES]).where(where_clause)

    component_f = flask.g.db_conn.execute(query).fetchone()

    if component_f is None:
        raise dci_exc.DCINotFound('Component File', f_id)

    res = flask.jsonify({'component_file': component_f})
    return res


@api.route('/components/<c_id>/files/<f_id>/content', methods=['GET'])
@auth.requires_auth({auth.AUTH_BASIC})
def download_component_file(user, c_id, f_id):
    swift = dci_config.get_store()

    def get_object(swift_object):
        for block in swift.get(swift_object)[1]:
            yield block

    component = v1_utils.verify_existence_and_get(c_id, _TABLE)
    v1_utils.verify_team_in_topic(user, component['topic_id'])
    COMPONENT_FILES = models.COMPONENT_FILES
    v1_utils.verify_existence_and_get(f_id, COMPONENT_FILES)
    auth.check_export_control(user, component)
    file_path = "%s/%s/%s" % (component['topic_id'], c_id, f_id)
    return flask.Response(get_object(file_path))


@api.route('/components/<c_id>/files', methods=['POST'])
@auth.requires_auth({auth.AUTH_BASIC})
def upload_component_file(user, c_id):
    if not(auth.is_admin(user)):
        raise auth.UNAUTHORIZED

    COMPONENT_FILES = models.COMPONENT_FILES

    component = v1_utils.verify_existence_and_get(c_id, _TABLE)

    file_id = utils.gen_uuid()
    file_path = "%s/%s/%s" % (component['topic_id'], c_id, file_id)

    swift = dci_config.get_store()
    swift.upload(file_path, flask.request.stream.read())
    s_file = swift.head(file_path)

    values = dict.fromkeys(['md5', 'mime', 'component_id', 'name'])

    values.update({
        'id': file_id,
        'component_id': c_id,
        'name': file_id,
        'created_at': datetime.datetime.utcnow().isoformat(),
        'md5': s_file['etag'],
        'mime': s_file['content-type'],
        'size': s_file['content-length']
    })

    query = COMPONENT_FILES.insert().values(**values)

    flask.g.db_conn.execute(query)
    result = json.dumps({'component_file': values})
    return flask.Response(result, 201, content_type='application/json')


@api.route('/components/<c_id>/files/<f_id>', methods=['DELETE'])
@auth.requires_auth({auth.AUTH_BASIC})
def delete_component_file(user, c_id, f_id):
    if not(auth.is_admin(user)):
        raise auth.UNAUTHORIZED

    COMPONENT_FILES = models.COMPONENT_FILES
    component = v1_utils.verify_existence_and_get(c_id, _TABLE)
    v1_utils.verify_existence_and_get(f_id, COMPONENT_FILES)

    where_clause = sql.or_(COMPONENT_FILES.c.id == f_id,
                           COMPONENT_FILES.c.name == f_id)

    query = COMPONENT_FILES.delete().where(where_clause)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIDeleteConflict('Component File', f_id)

    file_path = "%s/%s/%s" % (component['topic_id'], c_id, f_id)
    swift = dci_config.get_store()
    swift.delete(file_path)

    return flask.Response(None, 204, content_type='application/json')
