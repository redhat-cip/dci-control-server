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
                              'topic_id': topic_id,
                              'export_control': True}).data
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


def post_file(client, jobstate_id, file_desc):
    with mock.patch(SWIFT, spec=Swift) as mock_swift:

        mockito = mock.MagicMock()

        head_result = {
            'etag': utils.gen_etag(),
            'content-type': "stream",
            'content-length': 7
        }

        mockito.head.return_value = head_result
        mock_swift.return_value = mockito
        headers = {'DCI-JOBSTATE-ID': jobstate_id, 'DCI-NAME': file_desc.name,
                   'Content-Type': 'text/plain'}
        res = client.post('/api/v1/files',
                          headers=headers,
                          data=file_desc.content)

        return res.data['file']['id']


@mock.patch('jwt.api_jwt.datetime', spec=datetime.datetime)
def test_files(m_datetime, admin, user_sso_rh_employee, app, engine,
               jobstate_user_id):
    user_sso = user_sso_rh_employee
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime. \
        fromtimestamp(1518653629).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    with app.app_context():
        flask.g.db_conn = engine.connect()
        # get all files
        files = user_sso.get('/api/v1/files')
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
            file_id = post_file(admin, jobstate_user_id,
                                FileDesc('foo', content))

            get_file = user_sso.get('/api/v1/files/%s/content' % file_id)

            assert get_file.status_code == 200


