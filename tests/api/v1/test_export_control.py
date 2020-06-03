# -*- coding: utf-8 -*-
#
# Copyright (C) Red Hat, Inc
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

import mock
import six

from dci.common import utils
from dci.stores.swift import Swift

SWIFT = 'dci.stores.swift.Swift'


# team_user_id is exportable
def test_export_control_true(user, epm, team_user_id, topic_user_id):
    topic = epm.get('/api/v1/topics/%s' % topic_user_id).data['topic']
    epm.post('/api/v1/products/%s/teams' % topic['product_id'],
             data={'team_id': team_user_id})
    epm.put('/api/v1/topics/%s' % topic_user_id,
            data={'export_control': True},
            headers={'If-match': topic['etag']})
    topic = epm.get('/api/v1/topics/%s' % topic_user_id).data['topic']
    assert topic['export_control'] is True

    team = epm.get('/api/v1/teams/%s' % team_user_id).data['team']
    epm.put('/api/v1/teams/%s' % team_user_id,
            data={'exportable': True},
            headers={'If-match': team['etag']})
    team = epm.get('/api/v1/teams/%s' % team_user_id).data['team']
    assert team['exportable'] is True

    assert user.get('/api/v1/topics/%s/components' % topic_user_id).status_code == 200  # noqa

    team = epm.get('/api/v1/teams/%s' % team_user_id).data['team']
    epm.put('/api/v1/teams/%s' % team_user_id,
            data={'exportable': False},
            headers={'If-match': team['etag']})
    team = epm.get('/api/v1/teams/%s' % team_user_id).data['team']
    assert team['exportable'] is False
    assert user.get('/api/v1/topics/%s/components' % topic_user_id).status_code == 200  # noqa


def test_export_control_false(user, epm, team_user_id, topic_user_id):
    topic = epm.get('/api/v1/topics/%s' % topic_user_id).data['topic']
    epm.post('/api/v1/products/%s/teams' % topic['product_id'],
             data={'team_id': team_user_id})
    epm.put('/api/v1/topics/%s' % topic_user_id,
            data={'export_control': False},
            headers={'If-match': topic['etag']})
    topic = epm.get('/api/v1/topics/%s' % topic_user_id).data['topic']
    assert topic['export_control'] is False

    team = epm.get('/api/v1/teams/%s' % team_user_id).data['team']
    epm.put('/api/v1/teams/%s' % team_user_id,
            data={'exportable': True},
            headers={'If-match': team['etag']})
    team = epm.get('/api/v1/teams/%s' % team_user_id).data['team']
    assert team['exportable'] is True

    assert user.get('/api/v1/topics/%s/components' % topic_user_id).status_code == 200  # noqa

    team = epm.get('/api/v1/teams/%s' % team_user_id).data['team']
    epm.put('/api/v1/teams/%s' % team_user_id,
            data={'exportable': False},
            headers={'If-match': team['etag']})
    team = epm.get('/api/v1/teams/%s' % team_user_id).data['team']
    assert team['exportable'] is False
    assert user.get('/api/v1/topics/%s/components' % topic_user_id).status_code == 401  # noqa


def test_components_export_control_true(user, epm, team_user_id,
                                        topic_user_id, components_user_ids):
    topic = epm.get('/api/v1/topics/%s' % topic_user_id).data['topic']
    epm.put('/api/v1/topics/%s' % topic_user_id,
            data={'export_control': True},
            headers={'If-match': topic['etag']})
    topic = epm.get('/api/v1/topics/%s' % topic_user_id).data['topic']
    assert topic['export_control'] is True

    team = epm.get('/api/v1/teams/%s' % team_user_id).data['team']
    epm.put('/api/v1/teams/%s' % team_user_id,
            data={'exportable': False},
            headers={'If-match': team['etag']})

    with mock.patch(SWIFT, spec=Swift) as mock_swift:

        mockito = mock.MagicMock()
        mockito.get.return_value = ["test", six.StringIO("lollollel")]
        head_result = {
            'etag': utils.gen_etag(),
            'content-type': "stream",
            'content-length': 1
        }
        mockito.head.return_value = head_result
        mock_swift.return_value = mockito

        url = '/api/v1/components/%s/files' % components_user_ids[0]
        c_file = epm.post(url, data='lol')
        c_file_1_id = c_file.data['component_file']['id']

        # associated to the product thus it can access the topic's components
        assert user.get('/api/v1/components/%s' % components_user_ids[0]).status_code == 200  # noqa
        assert user.get('/api/v1/components/%s/files' % components_user_ids[0]).status_code == 200  # noqa
        assert user.get('/api/v1/components/%s/files/%s' % (components_user_ids[0], c_file_1_id)).status_code == 200  # noqa
        assert user.get('/api/v1/components/%s/files/%s/content' % (components_user_ids[0], c_file_1_id)).status_code == 200  # noqa


def test_components_export_control_false(user, epm, team_user_id,
                                         topic_user_id, components_user_ids):  # noqa
    topic = epm.get('/api/v1/topics/%s' % topic_user_id).data['topic']
    res = epm.put('/api/v1/topics/%s' % topic_user_id,
                  data={'export_control': False},
                  headers={'If-match': topic['etag']})
    assert res.status_code == 200
    topic = epm.get('/api/v1/topics/%s' % topic_user_id).data['topic']

    # exportable team should have full access to every topic even if
    # they are export_control=false
    team = epm.get('/api/v1/teams/%s' % team_user_id).data['team']
    epm.put('/api/v1/teams/%s' % team_user_id,
            data={'exportable': True},
            headers={'If-match': team['etag']})

    with mock.patch(SWIFT, spec=Swift) as mock_swift:

        mockito = mock.MagicMock()
        mockito.get.return_value = ["test", six.StringIO("lollollel")]
        head_result = {
            'etag': utils.gen_etag(),
            'content-type': "stream",
            'content-length': 1
        }
        mockito.head.return_value = head_result
        mock_swift.return_value = mockito

        url = '/api/v1/components/%s/files' % components_user_ids[0]
        c_file = epm.post(url, data='lol')
        c_file_1_id = c_file.data['component_file']['id']

        assert topic['export_control'] is False
        assert user.get('/api/v1/components/%s' % components_user_ids[0]).status_code == 200  # noqa
        assert user.get('/api/v1/components/%s/files' % components_user_ids[0]).status_code == 200  # noqa
        assert user.get('/api/v1/components/%s/files/%s' % (components_user_ids[0], c_file_1_id)).status_code == 200  # noqa
        assert user.get('/api/v1/components/%s/files/%s/content' % (components_user_ids[0], c_file_1_id)).status_code == 200  # noqa
