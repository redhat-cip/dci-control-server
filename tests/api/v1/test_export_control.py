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

# team_user_id is subscribing to topic_user_id


def test_topics_export_control_true(user, admin, team_user_id, topic_user_id):
    topic = admin.get('/api/v1/topics/%s' % topic_user_id).data['topic']

    admin.put('/api/v1/topics/%s' % topic_user_id,
              data={'export_control': True},
              headers={'If-match': topic['etag']})
    topic = admin.get('/api/v1/topics/%s' % topic_user_id).data['topic']
    assert topic['export_control'] is True
    # team_user_id is not subscribing to topic_user_id but it's root parent
    # is the team_product_id thus it can access topic's components
    assert user.get('/api/v1/topics/%s/components' % topic_user_id).status_code == 200 # noqa
    assert user.get('/api/v1/topics/%s/components/latest' % topic_user_id).status_code == 200 # noqa
    assert user.get('/api/v1/topics/%s/tests' % topic_user_id).status_code == 200 # noqa


def test_topics_export_control_false(user, admin, team_user_id, topic_user_id):
    topic = admin.get('/api/v1/topics/%s' % topic_user_id).data['topic']

    assert topic['export_control'] is False
    assert user.get('/api/v1/topics/%s/components' % topic_user_id).status_code == 200  # noqa
    assert user.get('/api/v1/topics/%s/components/latest' % topic_user_id).status_code == 200  # noqa
    assert user.get('/api/v1/topics/%s/tests' % topic_user_id).status_code == 200  # noqa

    # team_user_id is not subscribing to topic_user_id
    admin.delete('/api/v1/topics/%s/teams/%s' % (topic_user_id, team_user_id))
    assert user.get('/api/v1/topics/%s/components' % topic_user_id).status_code == 401  # noqa
    assert user.get('/api/v1/topics/%s/components/latest' % topic_user_id).status_code == 401  # noqa
    assert user.get('/api/v1/topics/%s/tests' % topic_user_id).status_code == 401  # noqa


def test_components_export_control_true(user, admin, team_user_id,
                                        topic_user_id, components_user_ids):
    topic = admin.get('/api/v1/topics/%s' % topic_user_id).data['topic']

    admin.put('/api/v1/topics/%s' % topic_user_id,
              data={'export_control': True},
              headers={'If-match': topic['etag']})
    topic = admin.get('/api/v1/topics/%s' % topic_user_id).data['topic']
    assert topic['export_control'] is True
    # team_user_id is not subscribing to topic_user_id but it's root parent
    # is the team_product_id thus it can access topic's components
    assert user.get('/api/v1/components/%s' % components_user_ids[0]).status_code == 200 # noqa


def test_components_export_control_false(user, admin, team_user_id,
                                         topic_user_id, components_user_ids): # noqa
    topic = admin.get('/api/v1/topics/%s' % topic_user_id).data['topic']

    assert topic['export_control'] is False
    assert user.get('/api/v1/components/%s' % components_user_ids[0]).status_code == 200 # noqa
    assert user.get('/api/v1/components/%s/files' % components_user_ids[0]).status_code == 200 # noqa

    # team_user_id is not subscribing to topic_user_id
    admin.delete('/api/v1/topics/%s/teams/%s' % (topic_user_id, team_user_id))
    assert user.get('/api/v1/components/%s' % components_user_ids[0]).status_code == 401 # noqa
    assert user.get('/api/v1/components/%s/files' % components_user_ids[0]).status_code == 401 # noqa
