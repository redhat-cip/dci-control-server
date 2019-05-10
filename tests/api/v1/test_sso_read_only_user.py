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

import flask

import collections
import datetime
import six
import uuid

import mock

from dci.common import utils
from dci.stores.swift import Swift
import tests.utils as t_utils

SWIFT = 'dci.stores.swift.Swift'
FileDesc = collections.namedtuple('FileDesc', ['name', 'content'])


# COMPONENTS
@mock.patch('jwt.api_jwt.datetime', spec=datetime.datetime)
def test_components(m_datetime, admin, user_sso_rh_employee, app, engine,
                    topic_id):
    user_sso = user_sso_rh_employee
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime. \
        fromtimestamp(1518653629).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    with app.app_context():
        flask.g.db_conn = engine.connect()
        pc = admin.post('/api/v1/components',
                        data={'name': 'pname%s' % uuid.uuid4(),
                              'type': 'gerrit_review',
                              'topic_id': topic_id}).data
        pc_id = pc['component']['id']
        # get all components of a topic
        cmpts = user_sso.get('/api/v1/topics/%s/components' % topic_id)
        assert cmpts.status_code == 200
        # get specific component
        cmpt = user_sso.get('/api/v1/components/%s' % pc_id)
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
            files = user_sso.get(url)
            # get components files
            assert files.status_code == 200
            c_file = admin.post(url, data='lol').data['component_file']

            url = '/api/v1/components/%s/files/%s/content' % (pc_id,
                                                              c_file['id'])
            # get component's file content
            d_file = user_sso.get(url)
            assert d_file.status_code == 200


# FILES
@mock.patch('jwt.api_jwt.datetime', spec=datetime.datetime)
def test_files(m_datetime, admin, user_sso_rh_employee, app, engine,
               jobstate_user_id, job_user_id):
    user_sso = user_sso_rh_employee
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime. \
        fromtimestamp(1518653629).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    with app.app_context():
        flask.g.db_conn = engine.connect()
        # get all files
        files = user_sso.get('/api/v1/jobs/%s/files' % job_user_id)
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

            get_file = user_sso.get('/api/v1/files/%s' % file_id)

            assert get_file.status_code == 200


# JOBS
@mock.patch('jwt.api_jwt.datetime', spec=datetime.datetime)
def test_jobs(m_datetime, user_sso_rh_employee, app, engine,
              remoteci_context, topic_user_id, components_user_ids):
    user_sso = user_sso_rh_employee
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime. \
        fromtimestamp(1518653629).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    with app.app_context():
        data = {'components_ids': components_user_ids,
                'topic_id': topic_user_id}
        job_1 = remoteci_context.post('/api/v1/jobs/schedule', data=data)
        # get all jobs
        db_all_jobs = user_sso.get('/api/v1/jobs?sort=created_at').data
        assert len(db_all_jobs['jobs']) > 0
        # get specific job
        job_id = job_1.data['job']['id']
        job = user_sso.get('/api/v1/jobs/%s' % job_id)
        assert job.status_code == 200

        # get job result
        job_result = user_sso.get('/api/v1/jobs/%s/results' % job_id)
        assert job_result.status_code == 200


# JOBSTATES
@mock.patch('jwt.api_jwt.datetime', spec=datetime.datetime)
def test_jobstates(m_datetime, user_sso_rh_employee, job_user_id, app, engine):
    user_sso = user_sso_rh_employee
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime. \
        fromtimestamp(1518653629).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    with app.app_context():
        # get all the jobstates
        jobstates = user_sso.get('/api/v1/jobs/%s/jobstates' % job_user_id)
        assert jobstates.status_code == 200


# PRODUCTS
@mock.patch('jwt.api_jwt.datetime', spec=datetime.datetime)
def test_products(m_datetime, user_sso_rh_employee, app, engine):
    user_sso = user_sso_rh_employee
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime. \
        fromtimestamp(1518653629).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    with app.app_context():
        # get all the products
        products = user_sso.get('/api/v1/products')
        assert products.status_code == 200


# TESTS
@mock.patch('jwt.api_jwt.datetime', spec=datetime.datetime)
def test_tests(m_datetime, admin, user_sso_rh_employee, app, engine,
               team_user_id):
    user_sso = user_sso_rh_employee
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime. \
        fromtimestamp(1518653629).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    with app.app_context():
        pt = admin.post('/api/v1/tests', data={'name': 'pname',
                                               'team_id': team_user_id}).data
        pt_id = pt['test']['id']

        # get by uuid
        created_t = user_sso.get('/api/v1/tests/%s' % pt_id)
        assert created_t.status_code == 200


# TOPICS
@mock.patch('jwt.api_jwt.datetime', spec=datetime.datetime)
def test_topics(m_datetime, user_sso_rh_employee, app, engine,
                topic_user_id):
    user_sso = user_sso_rh_employee
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime. \
        fromtimestamp(1518653629).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    with app.app_context():
        gtopic = user_sso.get('/api/v1/topics/%s' % topic_user_id)
        assert gtopic.status_code == 200
        gtopics = user_sso.get('/api/v1/topics')
        assert gtopics.status_code == 200


# GLOBAL STATUS
@mock.patch('jwt.api_jwt.datetime', spec=datetime.datetime)
def test_global_status(m_datetime, user_sso_rh_employee, app, engine):
    user_sso = user_sso_rh_employee
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime. \
        fromtimestamp(1518653629).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    with app.app_context():
        global_status = user_sso.get('/api/v1/global_status')
        assert global_status.status_code == 200
