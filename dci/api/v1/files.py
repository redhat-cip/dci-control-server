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

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import files_events
from dci.api.v1 import transformations as tsfm
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import embeds
from dci.db import models
from dci import dci_config
from dci.stores import files


_TABLE = models.FILES
# associate column names with the corresponding SA Column object
_FILES_FOLDER = dci_config.generate_conf()['FILES_UPLOAD_FOLDER']
_VALID_EMBED = embeds.files()
_FILES_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)
_EMBED_MANY = {
    'jobstate': False,
    'jobstate.job': False,
    'job': False,
    'team': False
}


def get_file_info_from_headers(headers):
    new_headers = {}
    for key, value in headers.items():
        key = key.lower().replace('dci-', '').replace('-', '_')
        if key in ['md5', 'mime', 'jobstate_id',
                   'job_id', 'name', 'test_id']:
            new_headers[key] = value
    return new_headers


@api.route('/files', methods=['POST'])
@decorators.login_required
def create_files(user):
    file_info = get_file_info_from_headers(dict(flask.request.headers))
    swift = dci_config.get_store('files')

    values = dict.fromkeys(['md5', 'mime', 'jobstate_id',
                            'job_id', 'name', 'test_id'])
    values.update(file_info)

    if values.get('jobstate_id') is None and values.get('job_id') is None:
        raise dci_exc.DCIException('HTTP headers DCI-JOBSTATE-ID or '
                                   'DCI-JOB-ID must be specified')
    if values.get('name') is None:
        raise dci_exc.DCIException('HTTP header DCI-NAME must be specified')

    if values['jobstate_id']:
        query = v1_utils.QueryBuilder(models.JOBSTATES)
        query.add_extra_condition(
            models.JOBSTATES.c.id == values['jobstate_id'])
        row = query.execute(fetchone=True)
        if row is None:
            raise dci_exc.DCINotFound('Jobstate', values['jobstate_id'])
        values['job_id'] = row['jobstates_job_id']

    query = v1_utils.QueryBuilder(models.JOBS)
    if not auth.is_admin(user):
        query.add_extra_condition(models.JOBS.c.team_id == user['team_id'])
    query.add_extra_condition(models.JOBS.c.id == values['job_id'])
    row = query.execute(fetchone=True)
    if row is None:
        raise dci_exc.DCINotFound('Job', values['job_id'])

    file_id = utils.gen_uuid()
    # ensure the directory which will contains the file actually exist

    file_path = swift.build_file_path(user['team_id'],
                                      values['job_id'],
                                      file_id)

    content = files.get_stream_or_content_from_request(flask.request)
    swift.upload(file_path, content)
    s_file = swift.head(file_path)

    etag = utils.gen_etag()
    values.update({
        'id': file_id,
        'created_at': datetime.datetime.utcnow().isoformat(),
        'updated_at': datetime.datetime.utcnow().isoformat(),
        'team_id': user['team_id'],
        'md5': None,
        'size': s_file['content-length'],
        'state': 'active',
        'etag': etag,
    })

    query = _TABLE.insert().values(**values)

    with flask.g.db_conn.begin():

        flask.g.db_conn.execute(query)
        result = json.dumps({'file': values})

        if values['mime'] == 'application/junit':
            _, file_descriptor = swift.get(file_path)
            junit = tsfm.junit2dict(file_descriptor.read())
            query = models.TESTS_RESULTS.insert().values({
                'id': utils.gen_uuid(),
                'created_at': values['created_at'],
                'updated_at': datetime.datetime.utcnow().isoformat(),
                'file_id': file_id,
                'job_id': values['job_id'],
                'name': values['name'],
                'success': junit['success'],
                'failures': junit['failures'],
                'errors': junit['errors'],
                'skips': junit['skips'],
                'total': junit['total'],
                'time': junit['time']
            })
            flask.g.db_conn.execute(query)
        files_events.create_event(file_id, models.FILES_CREATE)

    return flask.Response(result, 201, content_type='application/json')


@api.route('/files', methods=['GET'])
@decorators.login_required
def get_all_files(user, j_id=None):
    """Get all files.
    """
    args = schemas.args(flask.request.args.to_dict())

    query = v1_utils.QueryBuilder(_TABLE, args, _FILES_COLUMNS)

    # If it's not an admin then restrict the view to the team's file
    if not user.is_super_admin() and not user.is_rh_employee():
        query.add_extra_condition(_TABLE.c.team_id.in_(user.teams))
    if j_id is not None:
        query.add_extra_condition(_TABLE.c.job_id == j_id)
    query.add_extra_condition(_TABLE.c.state != 'archived')

    nb_rows = query.get_number_of_rows()
    rows = query.execute(fetchall=True)
    rows = v1_utils.format_result(rows, _TABLE.name, args['embed'],
                                  _EMBED_MANY)
    return json.jsonify({'files': rows, '_meta': {'count': nb_rows}})


@api.route('/files/<uuid:file_id>', methods=['GET'])
@decorators.login_required
def get_file_by_id(user, file_id):
    file = v1_utils.verify_existence_and_get(file_id, _TABLE)
    return base.get_resource_by_id(user, file, _TABLE, _EMBED_MANY)


@api.route('/files/<uuid:file_id>/content', methods=['GET'])
@decorators.login_required
def get_file_content(user, file_id):
    file = v1_utils.verify_existence_and_get(file_id, _TABLE)
    swift = dci_config.get_store('files')

    if not user.is_in_team(file['team_id']) and not user.is_rh_employee():
        raise auth.UNAUTHORIZED

    file_path = swift.build_file_path(file['team_id'],
                                      file['job_id'],
                                      file_id)

    # Check if file exist on the storage engine
    swift.head(file_path)
    _, file_descriptor = swift.get(file_path)
    return flask.send_file(
        file_descriptor,
        mimetype=file['mime'] or 'text/plain',
        as_attachment=True,
        attachment_filename=file['name'].replace(' ', '_')
    )


@api.route('/files/<uuid:file_id>', methods=['DELETE'])
@decorators.login_required
def delete_file_by_id(user, file_id):
    file = v1_utils.verify_existence_and_get(file_id, _TABLE)

    if not user.is_in_team(file['team_id']):
        raise auth.UNAUTHORIZED

    values = {'state': 'archived'}
    where_clause = _TABLE.c.id == file_id

    with flask.g.db_conn.begin():
        query = _TABLE.update().where(where_clause).values(**values)
        result = flask.g.db_conn.execute(query)

        if not result.rowcount:
            raise dci_exc.DCIDeleteConflict('File', file_id)
        files_events.create_event(file_id, models.FILES_DELETE)

        return flask.Response(None, 204, content_type='application/json')


@api.route('/files/purge', methods=['GET'])
@decorators.login_required
@decorators.has_role(['SUPER_ADMIN'])
def get_to_purge_archived_files(user):
    return base.get_to_purge_archived_resources(user, _TABLE)


@api.route('/files/purge', methods=['POST'])
@decorators.login_required
@decorators.has_role(['SUPER_ADMIN'])
def purge_archived_files(user):
    return base.purge_archived_resources(user, _TABLE)
