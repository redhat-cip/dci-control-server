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


def test_schedule_jobs_on_virtual_topic(admin, remoteci_context, team_user_id, product):
    # create virtual topic
    data = {'name': 'virtual_topic', 'product_id': product['id'],
            'component_types': [],
            'virtual': True}
    pt = admin.post('/api/v1/topics', data=data).data
    virtual_topic_id = pt['topic']['id']
    admin.post('/api/v1/topics/%s/teams' % virtual_topic_id, data={'team_id': team_user_id})  # noqa

    # create real topic 1
    data = {'name': 'real_topic_1', 'product_id': product['id'],
            'component_types': [],
            'virtual_topic_id': virtual_topic_id}
    pt = admin.post('/api/v1/topics', data=data).data
    real_topic_1_id = pt['topic']['id']

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
            'component_types': [],
            'virtual_topic_id': virtual_topic_id}
    pt = admin.post('/api/v1/topics', data=data).data
    real_topic_2_id = pt['topic']['id']

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

    # assert job belongs to real topic 2, then the scheduler
    # has done a rolled over the topics and get the latest one
    job = r.data['job']
    assert job['topic_id'] == real_topic_2_id


def test_schedule_jobs_on_real_topic(admin, remoteci_context, team_user_id, product):
    # create virtual topic
    data = {'name': 'virtual_topic', 'product_id': product['id'],
            'component_types': [],
            'virtual': True}
    pt = admin.post('/api/v1/topics', data=data).data
    virtual_topic_id = pt['topic']['id']

    # create real topic 1
    data = {'name': 'real_topic_1', 'product_id': product['id'],
            'component_types': [],
            'virtual_topic_id': virtual_topic_id}
    pt = admin.post('/api/v1/topics', data=data).data
    real_topic_1_id = pt['topic']['id']

    # schedule job on real topic 1
    # the team is not associated to real topic 1 and it's
    # export_control=False
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
    assert r.status_code == 401

    # add the team to the virtual topic
    admin.post('/api/v1/topics/%s/teams' % virtual_topic_id, data={'team_id': team_user_id})  # noqa

    r = remoteci_context.post(
        '/api/v1/jobs/schedule',
        headers=headers,
        data=data
    )
    # now it works because the team is associated to the virtual topic
    assert r.status_code == 201
    assert r.data['job']['topic_id'] == real_topic_1_id
