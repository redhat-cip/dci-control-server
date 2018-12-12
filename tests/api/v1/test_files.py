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

from __future__ import unicode_literals

import base64

import flask
import mock
import pytest

from dci import dci_config
from dci.api.v1 import files
from dci.api.v1.files import get_file_info_from_headers
from dci.common import exceptions as dci_exc
from dci.stores import files_utils
from tests import data as tests_data
import tests.utils as t_utils

import collections

FileDesc = collections.namedtuple('FileDesc', ['name', 'content'])


def test_create_files(user, jobstate_user_id):
    file_id = t_utils.post_file(user, jobstate_user_id,
                                FileDesc('kikoolol', 'content'))

    file = user.get('/api/v1/files/%s' % file_id).data['file']

    assert file['name'] == 'kikoolol'
    assert file['size'] == 7


def test_create_files_jobstate_id_and_job_id_missing(admin):
    file = admin.post('/api/v1/files', headers={'DCI-NAME': 'kikoolol'},
                      data='content')
    assert file.status_code == 400


def test_upload_tests_with_regressions_successfix(admin, remoteci_context,
                                                  remoteci, topic):
    headers = {
        'User-Agent': 'python-dciclient',
        'Client-Version': 'python-dciclient_0.1.0'
    }

    # 1. schedule two jobs and create their jobstate
    data = {'topic_id': topic['id'], 'remoteci_id': remoteci['id']}
    job_1 = remoteci_context.post('/api/v1/jobs/schedule',
                                  headers=headers,
                                  data=data).data['job']
    job_2 = remoteci_context.post('/api/v1/jobs/schedule',
                                  headers=headers,
                                  data=data).data['job']

    # 2. create the associated jobstates for each job
    data = {'job_id': job_1['id'], 'status': 'success'}
    jobstate_1 = admin.post('/api/v1/jobstates', data=data).data['jobstate']
    data = {'job_id': job_2['id'], 'status': 'failure'}
    jobstate_2 = admin.post('/api/v1/jobstates', data=data).data['jobstate']

    f_1 = t_utils.post_file(admin, jobstate_1['id'],
                            FileDesc('Tempest',
                                     tests_data.jobtest_one),
                            mime='application/junit')
    assert f_1 is not None
    t_utils.post_file(admin, jobstate_1['id'],
                      FileDesc('Rally',
                               tests_data.jobtest_one),
                      mime='application/junit')

    f_2 = t_utils.post_file(admin, jobstate_2['id'],
                            FileDesc('Tempest',
                                     tests_data.jobtest_two),
                            mime='application/junit')
    assert f_2 is not None
    t_utils.post_file(admin, jobstate_2['id'],
                      FileDesc('Rally',
                               tests_data.jobtest_one),
                      mime='application/junit')

    # 3. verify regression in job_2's result which is 'test_3'
    job_2_results = admin.get(
        '/api/v1/jobs/%s?embed=results' % job_2['id']).data['job']['results']
    for job_res in job_2_results:
        if job_res['name'] == 'Tempest':
            assert job_res['regressions'] == 1
            assert job_res['successfixes'] == 1
        elif job_res['name'] == 'Rally':
            assert job_res['regressions'] == 0
            assert job_res['successfixes'] == 0

    tcs = admin.get('/api/v1/files/%s/testscases' % f_2).data['testscases']
    assert tcs[0]['successfix']
    assert not tcs[0]['regression']
    assert not tcs[1]['successfix']
    assert not tcs[1]['regression']
    assert not tcs[2]['successfix']
    assert tcs[2]['regression']


def test_get_file_by_id(user, jobstate_user_id):
    file_id = t_utils.post_file(user, jobstate_user_id,
                                FileDesc('kikoolol', ''))

    # get by uuid
    created_file = user.get('/api/v1/files/%s' % file_id)
    assert created_file.status_code == 200
    assert created_file.data['file']['name'] == 'kikoolol'


def test_get_file_not_found(user):
    result = user.get('/api/v1/files/ptdr')
    assert result.status_code == 404


def test_get_file_with_embed(user, jobstate_user_id, team_user_id):
    pt = user.get('/api/v1/teams/%s' % team_user_id).data
    headers = {'DCI-JOBSTATE-ID': jobstate_user_id, 'DCI-NAME': 'kikoolol'}
    file = user.post('/api/v1/files', headers=headers).data

    file_id = file['file']['id']
    file['file']['team'] = pt['team']

    # verify embed
    file_embed = user.get('/api/v1/files/%s?embed=team' % file_id).data
    assert file == file_embed


def test_get_file_with_embed_not_valid(user, jobstate_user_id):
    file_id = t_utils.post_file(user, jobstate_user_id, FileDesc('name', ''))
    file = user.get('/api/v1/files/%s?embed=mdr' % file_id)
    assert file.status_code == 400


def test_delete_file_by_id(user, jobstate_user_id):
    file_id = t_utils.post_file(user, jobstate_user_id, FileDesc('name', ''))
    url = '/api/v1/files/%s' % file_id

    created_file = user.get(url)
    assert created_file.status_code == 200

    deleted_file = user.delete(url)
    assert deleted_file.status_code == 204

    gfile = user.get(url)
    assert gfile.status_code == 404


# Tests for the isolation


def test_create_file_as_user(user, jobstate_user_id):
    headers = {'DCI-JOBSTATE-ID': jobstate_user_id, 'DCI-NAME': 'name'}
    file = user.post('/api/v1/files', headers=headers)
    assert file.status_code == 201


def test_get_file_as_user(user, file_user_id, jobstate_user_id):
    file = user.get('/api/v1/files/%s' % file_user_id)
    assert file.status_code == 200


def test_delete_file_as_user(user, file_user_id):
    file_delete = user.delete('/api/v1/files/%s' % file_user_id)
    assert file_delete.status_code == 204


def test_get_file_content_as_user(user, jobstate_user_id):
    content = "azertyuiop1234567890"
    file_id = t_utils.post_file(user, jobstate_user_id,
                                FileDesc('foo', content))

    get_file = user.get('/api/v1/files/%s/content' % file_id)

    assert get_file.status_code == 200
    assert get_file.data == content


def test_change_file_to_invalid_state(admin, file_user_id):
    t = admin.get('/api/v1/files/' + file_user_id).data['file']
    data = {'state': 'kikoolol'}
    r = admin.put('/api/v1/files/' + file_user_id,
                  data=data,
                  headers={'If-match': t['etag']})
    assert r.status_code == 405
    current_file = admin.get('/api/v1/files/' + file_user_id)
    assert current_file.status_code == 200
    assert current_file.data['file']['state'] == 'active'


def test_get_file_info_from_header():
    headers = {
        'DCI-Client-Info': '',
        'DCI-Auth-Signature': '',
        'Authorization': '',
        'DCI-Datetime': '',
        'mime': '',
        'Dci-Job-Id': ''
    }
    file_info = get_file_info_from_headers(headers)
    assert len(file_info.keys()) == 2
    assert 'mime' in file_info
    assert 'job_id' in file_info


def test_build_certification():
    with open('tests/data/certification.xml.tar.gz', 'rb') as f:
        node_id = '40167'
        username = 'dci'
        password = 'dci'
        file_name = 'certification.xml.tar.gz'
        file_content = f.read()
        cert = files.build_certification(username, password, node_id,
                                         file_name, file_content)

        assert cert['username'] == 'dci'
        assert cert['password'] == 'dci'
        assert cert['id'] == '40167'
        assert cert['type'] == 'certification'
        assert cert['description'] == 'DCI automatic upload test log'
        assert cert['filename'] == 'certification.xml.tar.gz'

        base64.decodestring(cert['data'])


def test_get_previous_job_in_topic(app, user, remoteci_context,
                                   components_user_ids, team_user_id,
                                   engine):
    def get_new_remoteci_context():
        data = {'name': 'rname_new', 'team_id': team_user_id}
        remoteci = user.post('/api/v1/remotecis', data=data).data
        remoteci_id = str(remoteci['remoteci']['id'])
        api_secret = user.get('/api/v1/remotecis/%s' % remoteci_id).data
        api_secret = api_secret['remoteci']['api_secret']

        remoteci = {'id': remoteci_id, 'api_secret': api_secret,
                    'type': 'remoteci'}
        return t_utils.generate_token_based_client(app, remoteci)

    # job_1 from remoteci_context
    data = {
        'comment': 'kikoolol',
        'components': components_user_ids,
        'team_id': team_user_id
    }
    prev_job = remoteci_context.post('/api/v1/jobs', data=data).data
    prev_job_id = prev_job['job']['id']

    # adding a job in between from a new remoteci
    new_remoteci = get_new_remoteci_context()
    # job_2 from new remoteci
    new_remoteci.post('/api/v1/jobs', data=data)

    # job_3 from remoteci_context
    # prev(job_3) must be job_1 and not job_2
    new_job = remoteci_context.post('/api/v1/jobs', data=data).data
    new_job = new_job['job']
    with app.app_context():
        flask.g.db_conn = engine.connect()
        test_prev_job_id = str(files.get_previous_job_in_topic(new_job)['id'])
        assert prev_job_id == test_prev_job_id


def test_known_issues_in_tests(admin, user, job_user_id, topic_user_id):

    pissue = user.post('/api/v1/issues', data={'url': 'http://bugzilla/42',
                                               'topic_id': topic_user_id})
    pissue_id1 = pissue.data['issue']['id']
    pissue = user.post('/api/v1/issues', data={'url': 'http://bugzilla/43',
                                               'topic_id': topic_user_id})
    pissue_id2 = pissue.data['issue']['id']
    test = user.post('/api/v1/tests', data={'name': 'Testsuite_1:test_3'})
    test_id1 = test.data['test']['id']
    user.post('/api/v1/issues/%s/tests' % pissue_id1,
              data={'test_id': test_id1,
                    'topic_id': topic_user_id})
    user.post('/api/v1/issues/%s/tests' % pissue_id2,
              data={'test_id': test_id1,
                    'topic_id': topic_user_id})

    data = {'job_id': job_user_id, 'status': 'failure'}
    jobstate_1 = admin.post('/api/v1/jobstates', data=data).data['jobstate']
    file_id = t_utils.post_file(
        admin,
        jobstate_1['id'],
        FileDesc('Tempest', tests_data.jobtest_two),
        mime='application/junit'
    )
    testscases = admin.get(
        '/api/v1/files/%s/testscases' % file_id).data["testscases"]
    for testcase in testscases:
        if testcase['name'] == 'Testsuite_1:test_3':
            assert len(testcase['issues']) == 2
            issues_ids = {issue['id']
                          for issue in testcase['issues']}
            assert issues_ids == {pissue_id1, pissue_id2}


def test_purge(app, admin, user, jobstate_user_id, team_user_id, job_user_id):
    # create two files and archive them
    file_id1 = t_utils.post_file(user, jobstate_user_id,
                                 FileDesc('kikoolol', 'content'))
    user.delete('/api/v1/files/%s' % file_id1)
    file_id2 = t_utils.post_file(user, jobstate_user_id,
                                 FileDesc('kikoolol2', 'content2'))
    user.delete('/api/v1/files/%s' % file_id2)

    to_purge = admin.get('/api/v1/files/purge').data
    assert len(to_purge['files']) == 2
    admin.post('/api/v1/files/purge')
    path1 = files_utils.build_file_path(team_user_id, job_user_id, file_id1)
    store = dci_config.get_store('files')
    # the purge removed the file from the backend, get() must raise exception
    with pytest.raises(dci_exc.StoreExceptions):
        store.get(path1)
    path2 = files_utils.build_file_path(team_user_id, job_user_id, file_id2)
    with pytest.raises(dci_exc.StoreExceptions):
        store.get(path2)
    to_purge = admin.get('/api/v1/files/purge').data
    assert len(to_purge['files']) == 0


def test_purge_failure(app, admin, user, jobstate_user_id, job_user_id,
                       team_user_id):
    # create two files and archive them
    file_id1 = t_utils.post_file(user, jobstate_user_id,
                                 FileDesc('kikoolol', 'content'))
    user.delete('/api/v1/files/%s' % file_id1)
    file_id2 = t_utils.post_file(user, jobstate_user_id,
                                 FileDesc('kikoolol2', 'content2'))
    user.delete('/api/v1/files/%s' % file_id2)

    to_purge = admin.get('/api/v1/files/purge').data
    assert len(to_purge['files']) == 2

    # purge will fail
    with mock.patch('dci.stores.filesystem.FileSystem.delete') as mock_delete:
        mock_delete.side_effect = dci_exc.StoreExceptions('error')
        purge_res = admin.post('/api/v1/files/purge')
        assert purge_res.status_code == 400
        path1 = files_utils.build_file_path(team_user_id,
                                            job_user_id,
                                            file_id1)
        path2 = files_utils.build_file_path(team_user_id,
                                            job_user_id,
                                            file_id2)
        store = dci_config.get_store('files')
        store.get(path1)
        store.get(path2)
    to_purge = admin.get('/api/v1/files/purge').data
    assert len(to_purge['files']) == 2
