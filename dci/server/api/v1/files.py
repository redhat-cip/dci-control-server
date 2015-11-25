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
from dci.server.api.v1 import utils as v1_utils
from dci.server import auth2
from dci.server.common import exceptions as dci_exc
from dci.server.common import schemas
from dci.server.common import utils
from dci.server.db import models_core as models

# associate column names with the corresponding SA Column object
_FILES_COLUMNS = v1_utils.get_columns_name_with_objects(models.FILES)
_VALID_EMBED = {'jobstate': models.JOBSTATES,
                'jobstate.job': models.JOBS,
                'team': models.TEAMS}


def _verify_existence_and_get_file(js_id):
    return v1_utils.verify_existence_and_get(
        [models.FILES], js_id,
        sqlalchemy.sql.or_(models.FILES.c.id == js_id,
                           models.FILES.c.name == js_id))


@api.route('/files', methods=['POST'])
@auth2.requires_auth
def create_files():
    values = schemas.file.post(flask.request.json)

    etag = utils.gen_etag()
    values.update(
        {'id': utils.gen_uuid(),
         'created_at': datetime.datetime.utcnow().isoformat(),
         'updated_at': datetime.datetime.utcnow().isoformat(),
         'etag': etag}
    )

    query = models.FILES.insert().values(**values)

    flask.g.db_conn.execute(query)

    result = json.dumps({'file': values})
    return flask.Response(result, 201, headers={'ETag': etag},
                          content_type='application/json')


@api.route('/files/<file_id>', methods=['PUT'])
@auth2.requires_auth
def put_file(file_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    data_json = schemas.file.put(flask.request.json)

    _verify_existence_and_get_file(file_id)

    data_json['etag'] = utils.gen_etag()
    query = models.FILES.update().where(
        sqlalchemy.sql.and_(
            models.FILES.c.id == file_id,
            models.FILES.c.etag == if_match_etag)).values(**data_json)

    result = flask.g.db_conn.execute(query)

    if result.rowcount == 0:
        raise dci_exc.DCIException("Conflict on file '%s' or etag "
                                   "not matched." % file_id, status_code=409)

    return flask.Response(None, 204, headers={'ETag': data_json['etag']},
                          content_type='application/json')


@api.route('/files', methods=['GET'])
@auth2.requires_auth
def get_all_files():
    """Get all files.
    """
    args = schemas.args(flask.request.args.to_dict())
    embed = args['embed']

    v1_utils.verify_embed_list(embed, _VALID_EMBED.keys())

    # the default query with no parameters
    query = sqlalchemy.sql.select([models.FILES])

    # if embed then construct the query with a join
    if embed:
        query = v1_utils.get_query_with_join(models.FILES, [models.FILES],
                                             embed, _VALID_EMBED)

    query = v1_utils.sort_query(query, args['sort'], _FILES_COLUMNS)
    query = v1_utils.where_query(query, args['where'], models.FILES,
                                 _FILES_COLUMNS)

    # adds the limit/offset parameters
    query = query.limit(args['limit']).offset(args['offset'])

    # get the number of rows for the '_meta' section
    nb_row = utils.get_number_of_rows(models.FILES)

    rows = flask.g.db_conn.execute(query).fetchall()
    result = [v1_utils.group_embedded_resources(embed, row) for row in rows]

    result = {'files': result, '_meta': {'count': nb_row}}
    result = json.dumps(result, default=utils.json_encoder)
    return flask.Response(result, 200, content_type='application/json')


@api.route('/files/<file_id>', methods=['GET'])
@auth2.requires_auth
def get_file_by_id_or_name(file_id):
    embed = schemas.args(flask.request.args.to_dict())['embed']
    v1_utils.verify_embed_list(embed, _VALID_EMBED.keys())

    # the default query with no parameters
    query = sqlalchemy.sql.select([models.FILES])

    # if embed then construct the query with a join
    if embed:
        query = v1_utils.get_query_with_join(models.FILES, [models.FILES],
                                             embed, _VALID_EMBED)

    query = query.where(
        sqlalchemy.sql.or_(models.FILES.c.id == file_id,
                           models.FILES.c.name == file_id))

    row = flask.g.db_conn.execute(query).fetchone()
    if row is None:
        raise dci_exc.DCIException("File '%s' not found." % file_id,
                                   status_code=404)

    dfile = v1_utils.group_embedded_resources(embed, row)
    etag = dfile['etag']
    dfile = json.dumps({'file': dfile}, default=utils.json_encoder)
    return flask.Response(dfile, 200, headers={'ETag': etag},
                          content_type='application/json')


@api.route('/files/<file_id>', methods=['DELETE'])
@auth2.requires_auth
def delete_file_by_id(file_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    _verify_existence_and_get_file(file_id)

    query = models.FILES.delete().where(
        sqlalchemy.sql.and_(
            sqlalchemy.sql.or_(models.FILES.c.id == file_id,
                               models.FILES.c.name == file_id),
            models.FILES.c.etag == if_match_etag))

    result = flask.g.db_conn.execute(query)

    if result.rowcount == 0:
        raise dci_exc.DCIException("Files '%s' already deleted or "
                                   "etag not matched." % file_id,
                                   status_code=409)

    return flask.Response(None, 204, content_type='application/json')
