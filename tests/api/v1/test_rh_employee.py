# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Red Hat, Inc
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

import collections
import six
import uuid

import mock

from dci.common import utils
from dci.stores.swift import Swift
import tests.utils as t_utils

SWIFT = 'dci.stores.swift.Swift'
FileDesc = collections.namedtuple('FileDesc', ['name', 'content'])


# COMPONENTS
def test_components(admin, rh_employee, app, topic_id):
    pc = admin.post('/api/v1/components',
                    data={
                        'name': 'pname%s' % uuid.uuid4(),
                        'type': 'gerrit_review',
                        'topic_id': topic_id
                    }).data
    pc_id = pc['component']['id']
    # get all components of a topic
    cmpts = rh_employee.get('/api/v1/topics/%s/components' % topic_id)
    assert cmpts.status_code == 200
    # get specific component
    cmpt = rh_employee.get('/api/v1/components/%s' % pc_id)
    assert cmpt.status_code == 200
    # get component's files

    with mock.patch(SWIFT, spec=Swift) as mock_swift:

        mockito = mock.MagicMock()

        mockito.get.return_value = ["test", six.StringIO("lollollel")]
        head_result = {
            'etag': utils.gen_etag(),
            'content-type': "stream",
            'content-length': 3
        }
        mockito.head.return_value = head_result

        mock_swift.return_value = mockito

        url = '/api/v1/components/%s/files' % pc_id
        files = rh_employee.get(url)
        # get components files
        assert files.status_code == 200
        c_file = admin.post(url, data='lol').data['component_file']

        url = '/api/v1/components/%s/files/%s/content' % (pc_id, c_file['id'])
        # get component's file content
        d_file = rh_employee.get(url)
        assert d_file.status_code == 200


# FILES
def test_files(admin, rh_employee, app, jobstate_user_id, job_user_id):
    files = rh_employee.get('/api/v1/jobs/%s/files' % job_user_id)
    assert files.status_code == 200
    # get file content
    with mock.patch(SWIFT, spec=Swift) as mock_swift:

        mockito = mock.MagicMock()

        head_result = {
            'etag': utils.gen_etag(),
            'content-type': "stream",
            'content-length': 7
        }

        mockito.head.return_value = head_result
        mockito.get.return_value = [
            head_result, six.StringIO("azertyuiop1234567890")]
        mock_swift.return_value = mockito
        content = "azertyuiop1234567890"
        file_id = t_utils.post_file(admin, jobstate_user_id,
                                    FileDesc('foo', content))

        get_file = rh_employee.get('/api/v1/files/%s' % file_id)

        assert get_file.status_code == 200


# JOBS
def test_jobs(rh_employee, app, remoteci_context, topic_user_id, components_user_ids):
    data = {'components_ids': components_user_ids,
            'topic_id': topic_user_id}
    job_1 = remoteci_context.post('/api/v1/jobs/schedule', data=data)
    # get all jobs
    db_all_jobs = rh_employee.get('/api/v1/jobs?sort=created_at').data
    assert len(db_all_jobs['jobs']) > 0
    # get specific job
    job_id = job_1.data['job']['id']
    job = rh_employee.get('/api/v1/jobs/%s' % job_id)
    assert job.status_code == 200

    # get job result
    job_result = rh_employee.get('/api/v1/jobs/%s/results' % job_id)
    assert job_result.status_code == 200


# JOBSTATES
def test_jobstates(rh_employee, job_user_id, app):
    jobstates = rh_employee.get('/api/v1/jobs/%s/jobstates' % job_user_id)
    assert jobstates.status_code == 200


# PRODUCTS
def test_products(rh_employee, app):
    products = rh_employee.get('/api/v1/products')
    assert products.status_code == 200


# TESTS
def test_tests(admin, rh_employee, app, team_user_id):
    pt = admin.post(
        '/api/v1/tests',
        data={
            'name': 'pname',
            'team_id': team_user_id
        }
    ).data
    pt_id = pt['test']['id']

    # get by uuid
    created_t = rh_employee.get('/api/v1/tests/%s' % pt_id)
    assert created_t.status_code == 200


# TOPICS
def test_topics(rh_employee, app, topic_user_id):
    gtopic = rh_employee.get('/api/v1/topics/%s' % topic_user_id)
    assert gtopic.status_code == 200
    gtopics = rh_employee.get('/api/v1/topics')
    assert gtopics.status_code == 200


# GLOBAL STATUS
def test_global_status(rh_employee, app):
    global_status = rh_employee.get('/api/v1/global_status')
    assert global_status.status_code == 200
