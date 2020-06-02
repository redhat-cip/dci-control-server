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


def test_schedule_jobs_on_virtual_topic(admin, user, feeder_context, remoteci_context,
                                        team_user_id, product):

    # create virtual topic
    data = {'name': 'virtual_topic', 'product_id': product['id'],
            'component_types': [],
            'virtual': True}
    virtual_topic = admin.post('/api/v1/topics', data=data).data
    virtual_topic_id = virtual_topic['topic']['id']
    admin.post('/api/v1/topics/%s/teams' % virtual_topic_id, data={'team_id': team_user_id})  # noqa

    # create real topic 1
    data = {'name': 'real_topic_1', 'product_id': product['id'],
            'component_types': []}
    pt = admin.post('/api/v1/topics', data=data).data
    real_topic_1_id = pt['topic']['id']

    # schedule job on virtual topic
    # should fail because virtual topic is not associated to a real one
    headers = {
        'User-Agent': 'python-dciclient',
        'Client-Version': 'python-dciclient_0.1.0'
    }
    data = {'topic_id': virtual_topic_id}
    r = remoteci_context.post(
        '/api/v1/jobs/schedule',
        headers=headers,
        data=data
    )
    assert r.status_code == 412

    # update virtual topic with the real topic id
    ppt = feeder_context.put('/api/v1/topics/%s' % virtual_topic_id,
                             data={'real_topic_id': real_topic_1_id},
                             headers={'If-match': virtual_topic['topic']['etag']})
    assert ppt.status_code == 200

    # schedule job on virtual topic
    headers = {
        'User-Agent': 'python-dciclient',
        'Client-Version': 'python-dciclient_0.1.0'
    }
    data = {'topic_id': virtual_topic_id}
    r = remoteci_context.post(
        '/api/v1/jobs/schedule',
        headers=headers,
        data=data
    )
    assert r.status_code == 201

    # assert job belongs to real topic 1
    job = r.data['job']
    assert job['topic_id'] == real_topic_1_id

    # create real topic 2
    data = {'name': 'real_topic_2', 'product_id': product['id'],
            'component_types': []}
    pt = admin.post('/api/v1/topics', data=data).data
    real_topic_2_id = pt['topic']['id']

    # update virtual topic with the real topic id
    virtual_topic = user.get('/api/v1/topics/%s' % virtual_topic_id).data
    ppt = feeder_context.put('/api/v1/topics/%s' % virtual_topic_id,
                             data={'real_topic_id': real_topic_2_id},
                             headers={'If-match': virtual_topic['topic']['etag']})
    assert ppt.status_code == 200

    # schedule job on virtual topic
    headers = {
        'User-Agent': 'python-dciclient',
        'Client-Version': 'python-dciclient_0.1.0'
    }
    data = {'topic_id': virtual_topic_id}
    r = remoteci_context.post(
        '/api/v1/jobs/schedule',
        headers=headers,
        data=data
    )
    assert r.status_code == 201

    # assert job belongs to real topic 2
    job = r.data['job']
    assert job['topic_id'] == real_topic_2_id


def test_schedule_jobs_on_real_topic(admin, remoteci_context, team_user_id, product):
    # create real topic 1
    data = {'name': 'real_topic_1', 'product_id': product['id'],
            'component_types': []}
    pt = admin.post('/api/v1/topics', data=data).data
    real_topic_1_id = pt['topic']['id']

    # create virtual topic
    data = {'name': 'virtual_topic', 'product_id': product['id'],
            'component_types': [],
            'virtual': True,
            'real_topic_id': real_topic_1_id}
    pt = admin.post('/api/v1/topics', data=data)
    assert pt.status_code == 201

    # schedule job on real topic 1
    # real topic 1 is export_control=False but the
    # team_user_id is exportable
    headers = {
        'User-Agent': 'python-dciclient',
        'Client-Version': 'python-dciclient_0.1.0'
    }
    data = {'topic_id': real_topic_1_id}
    r = remoteci_context.post(
        '/api/v1/jobs/schedule',
        headers=headers,
        data=data
    )
    # it does not work because the team is not associated to the virtual topic
    assert r.status_code == 201
    assert r.data['job']['topic_id'] == real_topic_1_id
