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
import base64
import datetime

try:
    from xmlrpclib import ServerProxy
except ImportError:
    from xmlrpc.client import ServerProxy

import flask
from flask import json

from dci.api.v1 import api
from dci.api.v1 import base
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
from swiftclient import exceptions as swift_exc

from sqlalchemy import sql

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


def _get_test_result_of_previous_job(job):
    def _get_previous_job_in_topic(job):
        topic_id = job['topic_id']
        query = sql.select([models.JOBS]). \
            where(sql.and_(models.JOBS.c.topic_id == topic_id,
                           models.JOBS.c.created_at < job['created_at'],
                           models.JOBS.c.id != job['id'],
                           models.JOBS.c.state != 'archived')). \
            order_by(sql.desc(models.JOBS.c.created_at))
        return flask.g.db_conn.execute(query).fetchone()

    prev_job = _get_previous_job_in_topic(job)
    if prev_job is None:
        return None
    query = sql.select([models.TESTS_RESULTS]). \
        where(models.TESTS_RESULTS.c.job_id == prev_job['id'])
    res = flask.g.db_conn.execute(query).fetchone()
    if res is not None:
        res = dict(res)
    return res


@api.route('/files', methods=['POST'])
@decorators.login_required
@decorators.check_roles
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
    job = query.execute(fetchone=True, use_labels=False)
    if job is None:
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
            jsonunit = tsfm.junit2dict(file_descriptor.read())
            prev_testresult = _get_test_result_of_previous_job(job)
            if prev_testresult is not None:
                prev_testresult['testscases'] = prev_testresult['tests_cases']
                if len(prev_testresult['testscases']) > 0:
                    tsfm.add_regressions_and_successfix_to_tests(
                        prev_testresult, jsonunit)
            query = models.TESTS_RESULTS.insert().values({
                'id': utils.gen_uuid(),
                'created_at': values['created_at'],
                'updated_at': datetime.datetime.utcnow().isoformat(),
                'file_id': file_id,
                'job_id': values['job_id'],
                'name': values['name'],
                'success': jsonunit['success'],
                'failures': jsonunit['failures'],
                'errors': jsonunit['errors'],
                'regressions': jsonunit['regressions'],
                'skips': jsonunit['skips'],
                'total': jsonunit['total'],
                'time': jsonunit['time'],
                'tests_cases': jsonunit['testscases']
            })
            flask.g.db_conn.execute(query)

    return flask.Response(result, 201, content_type='application/json')


@api.route('/files', methods=['GET'])
@decorators.login_required
@decorators.check_roles
def get_all_files(user, j_id=None):
    """Get all files.
    """
    args = schemas.args(flask.request.args.to_dict())

    query = v1_utils.QueryBuilder(_TABLE, args, _FILES_COLUMNS)

    # If it's not an admin then restrict the view to the team's file
    if not user.is_super_admin() and not user.is_read_only_user():
        query.add_extra_condition(_TABLE.c.team_id.in_(user.teams_ids))
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
@decorators.check_roles
def get_file_by_id(user, file_id):
    file = v1_utils.verify_existence_and_get(file_id, _TABLE)
    return base.get_resource_by_id(user, file, _TABLE, _EMBED_MANY)


def get_file_descriptor(file_object):
    swift = dci_config.get_store('files')
    file_path = swift.build_file_path(file_object['team_id'],
                                      file_object['job_id'],
                                      file_object['id'])
    # Check if file exist on the storage engine
    swift.head(file_path)
    _, file_descriptor = swift.get(file_path)
    return file_descriptor


def get_file_object(file_id):
    return v1_utils.verify_existence_and_get(file_id, _TABLE)


@api.route('/files/<uuid:file_id>/content', methods=['GET'])
@decorators.login_required
@decorators.check_roles
def get_file_content(user, file_id):
    file = get_file_object(file_id)
    if not user.is_in_team(file['team_id']) and not user.is_read_only_user():
        raise auth.UNAUTHORIZED
    file_descriptor = get_file_descriptor(file)
    return flask.send_file(
        file_descriptor,
        mimetype=file['mime'] or 'text/plain',
        as_attachment=True,
        attachment_filename=file['name'].replace(' ', '_')
    )


@api.route('/files/<uuid:file_id>', methods=['DELETE'])
@decorators.login_required
@decorators.check_roles
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

        return flask.Response(None, 204, content_type='application/json')


def build_certification(username, password, node_id, file_name, file_content):
    return {
        'username': username,
        'password': password,
        'id': node_id,
        'type': 'certification',
        'data': base64.b64encode(file_content),
        'description': 'DCI automatic upload test log',
        'filename': file_name
    }


@api.route('/files/<uuid:file_id>/certifications', methods=['POST'])
@decorators.login_required
@decorators.check_roles
def upload_certification(user, file_id):
    data = schemas.file_upload_certification.post(flask.request.json)

    file = get_file_object(file_id)
    file_descriptor = get_file_descriptor(file)
    file_content = file_descriptor.read()

    username = data['username']
    password = data['password']
    conf = dci_config.generate_conf()
    proxy = ServerProxy(conf['CERTIFICATION_URL'])
    certification_details = proxy.Cert.getOpenStack_4_7({
        'username': username,
        'password': password,
        'certification_id': data['certification_id']
    })
    certification = build_certification(
        username,
        password,
        certification_details['cert_nid'],
        file['name'],
        file_content
    )
    proxy.Cert.uploadTestLog(certification)
    return flask.Response(None, 204, content_type='application/json')


@api.route('/files/purge', methods=['GET'])
@decorators.login_required
@decorators.check_roles
def get_to_purge_archived_files(user):
    return base.get_to_purge_archived_resources(user, _TABLE)


@api.route('/files/purge', methods=['POST'])
@decorators.login_required
@decorators.check_roles
def purge_archived_files(user):

    try:
        swift = dci_config.get_store('files')
        query = sql.select([_TABLE]).where(_TABLE.c.state == 'archived')
        files = flask.g.db_conn.execute(query).fetchall()
        for file in files:
            file_path = swift.build_file_path(user['team_id'], file['job_id'],
                                              file['id'])
            swift.delete(file_path)
    except swift_exc.ClientException as e:
        if e.http_status == 404:
            pass
        else:
            raise e

    return base.purge_archived_resources(user, _TABLE)
