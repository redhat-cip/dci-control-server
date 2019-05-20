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
from dci.api.v1 import tests
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common.schemas2 import (
    check_json_is_valid,
    file_upload_certification_schema,
    check_and_get_args
)
from dci.common import utils
from dci.db import embeds
from dci.db import models
from dci import dci_config
from dci.stores import files_utils
import logging

from sqlalchemy import sql
from sqlalchemy import exc as sa_exc

LOG = logging.getLogger(__name__)
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


def get_previous_job_in_topic(job):
    topic_id = job['topic_id']
    query = sql.select([models.JOBS]). \
        where(sql.and_(models.JOBS.c.topic_id == topic_id,
                       models.JOBS.c.created_at < job['created_at'],
                       models.JOBS.c.id != job['id'],
                       models.JOBS.c.remoteci_id == job['remoteci_id'],
                       models.JOBS.c.state != 'archived')). \
        order_by(sql.desc(models.JOBS.c.created_at))
    return flask.g.db_conn.execute(query).fetchone()


def _get_previous_jsonunit(job, filename):
    prev_job = get_previous_job_in_topic(job)
    if prev_job is None:
        return None
    query = sql.select([models.TESTS_RESULTS]). \
        where(sql.and_(models.TESTS_RESULTS.c.job_id == prev_job['id'],
                       models.TESTS_RESULTS.c.name == filename))
    res = flask.g.db_conn.execute(query).fetchone()
    if res is None:
        return None
    test_file = get_file_object(res.file_id)
    file_descriptor = get_file_descriptor(test_file)
    return tsfm.junit2dict(file_descriptor.read())


def _compute_regressions_successfix(jsonunit, previous_jsonunit):
    if previous_jsonunit and len(previous_jsonunit['testscases']) > 0:
        return tsfm.add_regressions_and_successfix_to_tests(
            previous_jsonunit,
            jsonunit
        )
    return jsonunit


def _compute_known_tests_cases(jsonunit, job):
    tests_to_issues = tests.get_tests_to_issues(job['topic_id'])
    return tsfm.add_known_issues_to_tests(jsonunit, tests_to_issues)


def _process_junit_file(values, junit_content, job):
    jsonunit = tsfm.junit2dict(junit_content)
    previous_jsonunit = _get_previous_jsonunit(job, values['name'])

    jsonunit = _compute_regressions_successfix(jsonunit, previous_jsonunit)
    jsonunit = _compute_known_tests_cases(jsonunit, job)

    query = models.TESTS_RESULTS.insert().values({
        'id': utils.gen_uuid(),
        'created_at': values['created_at'],
        'updated_at': datetime.datetime.utcnow().isoformat(),
        'file_id': values['id'],
        'job_id': job['id'],
        'name': values['name'],
        'success': jsonunit['success'],
        'failures': jsonunit['failures'],
        'errors': jsonunit['errors'],
        'regressions': jsonunit['regressions'],
        'successfixes': jsonunit['successfixes'],
        'skips': jsonunit['skips'],
        'total': jsonunit['total'],
        'time': jsonunit['time']
    })

    flask.g.db_conn.execute(query)


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
    values = dict.fromkeys(['md5', 'mime', 'jobstate_id',
                            'job_id', 'name', 'test_id'])
    values.update(file_info)

    if values.get('jobstate_id') is None and values.get('job_id') is None:
        raise dci_exc.DCIException('HTTP headers DCI-JOBSTATE-ID or '
                                   'DCI-JOB-ID must be specified')
    if values.get('name') is None:
        raise dci_exc.DCIException('HTTP header DCI-NAME must be specified')

    if values.get('jobstate_id') and values.get('job_id') is None:
        jobstate = v1_utils.verify_existence_and_get(values.get('jobstate_id'),
                                                     models.JOBSTATES)
        values['job_id'] = jobstate['job_id']

    job = v1_utils.verify_existence_and_get(values.get('job_id'), models.JOBS)
    if user.is_not_in_team(job['team_id']) or user.is_read_only_user():
        raise dci_exc.Unauthorized()

    file_id = utils.gen_uuid()
    file_path = files_utils.build_file_path(job['team_id'],
                                            values['job_id'],
                                            file_id)

    content = files_utils.get_stream_or_content_from_request(flask.request)
    store = dci_config.get_store('files')
    store.upload(file_path, content)
    s_file = store.head(file_path)

    etag = utils.gen_etag()
    values.update({
        'id': file_id,
        'created_at': datetime.datetime.utcnow().isoformat(),
        'updated_at': datetime.datetime.utcnow().isoformat(),
        'team_id': job['team_id'],
        'md5': None,
        'size': s_file['content-length'],
        'state': 'active',
        'etag': etag,
    })

    with flask.g.db_conn.begin():
        q_insert_file = _TABLE.insert().values(**values)
        flask.g.db_conn.execute(q_insert_file)
        result = json.dumps({'file': values})

        if values['mime'] == 'application/junit':
            junit_content = store.get(file_path)[1].read()
            _process_junit_file(values, junit_content, job)

    return flask.Response(result, 201, content_type='application/json')


def get_all_files(user, job_id):
    """Get all files.
    """
    args = check_and_get_args(flask.request.args.to_dict())
    job = v1_utils.verify_existence_and_get(job_id, models.JOBS)
    if user.is_not_super_admin() and user.is_not_read_only_user():
        if (job['team_id'] not in user.teams_ids and
            job['team_id'] not in user.child_teams_ids):
            raise dci_exc.Unauthorized()

    query = v1_utils.QueryBuilder(_TABLE, args, _FILES_COLUMNS)

    query.add_extra_condition(_TABLE.c.job_id == job_id)
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


def get_file_descriptor(file_object):
    store = dci_config.get_store('files')
    file_path = files_utils.build_file_path(file_object['team_id'],
                                            file_object['job_id'],
                                            file_object['id'])
    # Check if file exist on the storage engine
    store.head(file_path)
    _, file_descriptor = store.get(file_path)
    return file_descriptor


def get_file_object(file_id):
    return v1_utils.verify_existence_and_get(file_id, _TABLE)


@api.route('/files/<uuid:file_id>/content', methods=['GET'])
@decorators.login_required
def get_file_content(user, file_id):
    file = get_file_object(file_id)
    if not user.is_in_team(file['team_id']) and not user.is_read_only_user():
        raise dci_exc.Unauthorized()
    file_descriptor = get_file_descriptor(file)
    return flask.send_file(
        file_descriptor,
        mimetype=file['mime'] or 'text/plain',
        as_attachment=True,
        attachment_filename=file['name'].replace(' ', '_')
    )


@api.route('/files/<uuid:file_id>/testscases', methods=['GET'])
@decorators.login_required
def get_file_testscases(user, file_id):
    file = get_file_object(file_id)
    if not user.is_in_team(file['team_id']) and not user.is_read_only_user():
        raise dci_exc.Unauthorized()
    file_descriptor = get_file_descriptor(file)
    jsonunit = tsfm.junit2dict(file_descriptor.read())
    job = v1_utils.verify_existence_and_get(file['job_id'], models.JOBS)
    previous_jsonunit = _get_previous_jsonunit(job, file['name'])
    jsonunit = _compute_regressions_successfix(jsonunit, previous_jsonunit)
    return flask.Response(json.dumps({
        "testscases": jsonunit["testscases"]
    }), 200, content_type='application/json')


@api.route('/files/<uuid:file_id>', methods=['DELETE'])
@decorators.login_required
def delete_file_by_id(user, file_id):
    file = v1_utils.verify_existence_and_get(file_id, _TABLE)

    if not user.is_in_team(file['team_id']):
        raise dci_exc.Unauthorized()

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
def upload_certification(user, file_id):
    data = flask.request.json
    check_json_is_valid(file_upload_certification_schema, data)

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
def get_to_purge_archived_files(user):
    return base.get_to_purge_archived_resources(user, _TABLE)


@api.route('/files/purge', methods=['POST'])
@decorators.login_required
def purge_archived_files(user):

    # get all archived files
    archived_files = base.get_archived_resources(_TABLE)

    store = dci_config.get_store('files')

    # for each file delete it from within a transaction
    # if the SQL deletion or the Store deletion fail then
    # rollback the transaction, otherwise commit.
    for file in archived_files:
        tx = flask.g.db_conn.begin()
        try:
            q_delete_file = _TABLE.delete().where(_TABLE.c.id == file['id'])
            flask.g.db_conn.execute(q_delete_file)
            file_path = files_utils.build_file_path(file['team_id'],
                                                    file['job_id'],
                                                    file['id'])
            store.delete(file_path)
            tx.commit()
            LOG.debug('file %s removed' % file_path)
        except dci_exc.StoreExceptions as e:
            if e.status_code == 404:
                LOG.warn('file %s not found in store' % file_path)
            else:
                raise e
        except sa_exc.DBAPIError as e:
            LOG.error('Error while removing file %s, message: %s'
                      % (file_path, str(e)))
            tx.rollback()
            raise dci_exc.DCIException(str(e))

    return flask.Response(None, 204, content_type='application/json')
