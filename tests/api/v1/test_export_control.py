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

# team_user_id is subscribing to topic_user_id


def test_topics_export_control_true(user, epm, team_user_id, topic_user_id):
    topic = epm.get('/api/v1/topics/%s' % topic_user_id).data['topic']
    epm.delete('/api/v1/topics/%s/teams/%s' % (topic_user_id, team_user_id))
    epm.delete('/api/v1/products/%s/teams/%s' % (topic['product_id'], team_user_id))
    assert user.get('/api/v1/topics/%s/components' % topic_user_id).status_code == 401  # noqa

    res = epm.post('/api/v1/products/%s/teams' % topic['product_id'],
                   data={'team_id': team_user_id})
    assert res.status_code == 201

    epm.put('/api/v1/topics/%s' % topic_user_id,
            data={'export_control': True},
            headers={'If-match': topic['etag']})
    topic = epm.get('/api/v1/topics/%s' % topic_user_id).data['topic']
    assert topic['export_control'] is True
    # team_user_id is associated to the product and the topic is exported
    # then it should have access to the topic's components
    assert user.get('/api/v1/topics/%s/components' % topic_user_id).status_code == 200  # noqa


def test_topics_export_control_false(user, epm, team_user_id, topic_user_id):
    topic = epm.get('/api/v1/topics/%s' % topic_user_id).data['topic']
    assert topic['export_control'] is False
    epm.delete('/api/v1/topics/%s/teams/%s' % (topic_user_id, team_user_id))
    epm.delete('/api/v1/products/%s/teams/%s' % (topic['product_id'], team_user_id))

    # team_user_id is not associated to the product nor to the topic
    assert user.get('/api/v1/topics/%s/components' % topic_user_id).status_code == 401  # noqa

    # team_user_id is associated to the product but not to the topic
    epm.post('/api/v1/products/%s/teams' % topic['product_id'], data={'team_id': team_user_id})  # noqa
    epm.delete('/api/v1/topics/%s/teams/%s' % (topic_user_id, team_user_id))
    assert user.get('/api/v1/topics/%s/components' % topic_user_id).status_code == 401  # noqa


def test_nrt_product_export_control_true(admin, user, epm, team_user_id, topic_user_id):
    """ this nrt test highlight the case when a team is associated to a random
    product then it can access every topics with export_control=true regardless
    of the product association
    """
    topic = epm.get('/api/v1/topics/%s' % topic_user_id).data['topic']
    epm.put('/api/v1/topics/%s' % topic_user_id,
            data={'export_control': True},
            headers={'If-match': topic['etag']})

    # create aside project and assign the team_user_id to it
    data = {
        'name': 'name',
        'label': 'LABEL',
        'description': 'description'
    }
    result = admin.post('/api/v1/products', data=data)
    res = epm.post('/api/v1/products/%s/teams' % result.data['product']['id'],
                   data={'team_id': team_user_id})
    assert res.status_code == 201

    epm.delete('/api/v1/topics/%s/teams/%s' % (topic_user_id, team_user_id))
    epm.delete('/api/v1/products/%s/teams/%s' % (topic['product_id'], team_user_id))

    # team_user_id is not associated to the product nor to the topic
    assert user.get('/api/v1/topics/%s/components' % topic_user_id).status_code == 401  # noqa


def test_nrt_topic_export_control_false(admin, user, epm, team_user_id, topic_user_id):
    """ this nrt test highlight the case when a team is associated to a random
    topic of a product then it can access every topics with regardless of the
    topic association
    """
    topic = epm.get('/api/v1/topics/%s' % topic_user_id).data['topic']
    assert topic['export_control'] is False

    epm.delete('/api/v1/topics/%s/teams/%s' % (topic_user_id, team_user_id))

    # team_user_id is not associated to the product nor to the topic
    assert user.get('/api/v1/topics/%s/components' % topic_user_id).status_code == 401  # noqa

    # associate team_user_id to another topic
    data = {'name': 'tname', 'product_id': topic['product_id'],
            'component_types': ['type1', 'type2']}
    pt = epm.post('/api/v1/topics', data=data).data
    another_topic = pt['topic']
    assert another_topic['export_control'] is False
    res = epm.post('/api/v1/topics/%s/teams/' % another_topic['id'],
                   data={'team_id': team_user_id})
    assert res.status_code == 201

    # team_user_id is not associated to the product nor to the topic
    assert user.get('/api/v1/topics/%s/components' % topic_user_id).status_code == 401  # noqa


def test_components_export_control_true(user, epm, team_user_id,
                                        topic_user_id, components_user_ids):
    topic = epm.get('/api/v1/topics/%s' % topic_user_id).data['topic']
    res = epm.post('/api/v1/products/%s/teams' % topic['product_id'],
                   data={'team_id': team_user_id})
    assert res.status_code == 201
    epm.put('/api/v1/topics/%s' % topic_user_id,
            data={'export_control': True},
            headers={'If-match': topic['etag']})
    topic = epm.get('/api/v1/topics/%s' % topic_user_id).data['topic']
    assert topic['export_control'] is True

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
        # team_user_id is not subscribing to topic_user_id but it's
        # associated to the product thus it can access the topic's components
        assert user.get('/api/v1/components/%s' % components_user_ids[0]).status_code == 200  # noqa
        assert user.get('/api/v1/components/%s/files' % components_user_ids[0]).status_code == 200  # noqa
        assert user.get('/api/v1/components/%s/files/%s' % (components_user_ids[0], c_file_1_id)).status_code == 200  # noqa
        assert user.get('/api/v1/components/%s/files/%s/content' % (components_user_ids[0], c_file_1_id)).status_code == 200  # noqa


def test_components_export_control_false(user, epm, team_user_id,
                                         topic_user_id, components_user_ids):  # noqa
    topic = epm.get('/api/v1/topics/%s' % topic_user_id).data['topic']
    res = epm.post('/api/v1/products/%s/teams' % topic['product_id'],
                   data={'team_id': team_user_id})
    assert res.status_code == 201

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

        # team_user_id is associated to the product but not to the topic,
        # since the topic is not exported the user doesn't have the access
        epm.delete('/api/v1/topics/%s/teams/%s' % (topic_user_id, team_user_id))  # noqa
        assert user.get('/api/v1/components/%s' % components_user_ids[0]).status_code == 401  # noqa
        assert user.get('/api/v1/components/%s/files' % components_user_ids[0]).status_code == 401  # noqa
        assert user.get('/api/v1/components/%s/files/%s' % (components_user_ids[0], c_file_1_id)).status_code == 401  # noqa
        assert user.get('/api/v1/components/%s/files/%s/content' % (components_user_ids[0], c_file_1_id)).status_code == 401  # noqa
