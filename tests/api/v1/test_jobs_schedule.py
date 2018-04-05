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


def test_schedule_jobs(remoteci_context, remoteci, topic):
    headers = {
        'User-Agent': 'python-dciclient',
        'Client-Version': 'python-dciclient_0.1.0'
    }
    data = {'topic_id': topic['id']}
    r = remoteci_context.post(
        '/api/v1/jobs/schedule',
        headers=headers,
        data=data
    )
    assert r.status_code == 201
    job = r.data['job']
    assert job['topic_id'] == topic['id']
    assert job['user_agent'] == headers['User-Agent']
    assert job['client_version'] == headers['Client-Version']
    assert job['rconfiguration_id'] is None


def test_schedule_jobs_with_components_ids(user, remoteci_context, topic):
    components = user.get('/api/v1/topics/%s/components' % topic['id']).data['components']  # noqa
    data = {
        'topic_id': topic['id'],
        'components_ids': [components[0]['id']]
    }
    r = remoteci_context.post(
        '/api/v1/jobs/schedule',
        data=data
    )
    assert r.status_code == 201


def _create_rconfiguration(admin, remoteci_id, data):
    url = '/api/v1/remotecis/%s/rconfigurations' % remoteci_id
    r = admin.post(url, data=data)
    assert r.status_code == 201
    return r.data['rconfiguration']


def test_schedule_jobs_with_rconfiguration(admin, remoteci_context, topic):
    remoteci = remoteci_context.get('/api/v1/identity').data['identity']
    rconfiguration = {'name': 'rc', 'topic_id': topic['id']}
    _create_rconfiguration(admin, remoteci['id'], rconfiguration)
    data = {
        'topic_id': topic['id'],
    }
    r = remoteci_context.post(
        '/api/v1/jobs/schedule',
        data=data
    )
    assert r.status_code == 201


def _update_remoteci(admin, id, etag, data):
    url = '/api/v1/remotecis/%s' % id
    r = admin.put(url, headers={'If-match': etag}, data=data)
    assert r.status_code == 204
    return admin.get(url).data['remoteci']


def test_schedule_jobs_on_remoteci_inactive(admin, remoteci_context,
                                            remoteci_user_id, topic):
    remoteci = remoteci_context.get('/api/v1/identity').data['identity']
    remoteci['etag'] = admin.get(
        '/api/v1/remotecis/%s' % remoteci['id']).data['remoteci']['etag']

    remoteci = _update_remoteci(admin, remoteci['id'], remoteci['etag'],
                                {'state': 'inactive'})
    data = {'topic_id': topic['id']}
    r = remoteci_context.post('/api/v1/jobs/schedule', data=data)
    assert r.status_code != 201

    remoteci = _update_remoteci(admin, remoteci['id'], remoteci['etag'],
                                {'state': 'active'})
    data = {'topic_id': topic['id']}
    r = remoteci_context.post('/api/v1/jobs/schedule', data=data)
    assert r.status_code == 201


def _update_topic(admin, topic, data):
    url = '/api/v1/topics/%s' % topic['id']
    r = admin.put(url, headers={'If-match': topic['etag']}, data=data)
    assert r.status_code == 204
    return admin.get(url).data['topic']


def test_schedule_jobs_on_topic_inactive(admin, remoteci_context, remoteci,
                                         topic):
    topic = _update_topic(admin, topic, {'state': 'inactive'})
    data = {'topic_id': topic['id']}
    r = remoteci_context.post('/api/v1/jobs/schedule', data=data)
    assert r.status_code == 412

    topic = _update_topic(admin, topic, {'state': 'active'})
    data = {'topic_id': topic['id']}
    r = remoteci_context.post('/api/v1/jobs/schedule', data=data)
    assert r.status_code == 201


def test_schedule_jobs_kills_old_jobs(admin, remoteci_context, topic):
    data = {'topic_id': topic['id']}
    r = remoteci_context.post('/api/v1/jobs/schedule', data=data)
    assert r.status_code == 201
    r = remoteci_context.post('/api/v1/jobs/schedule', data=data)
    assert r.status_code == 201
    jobs = admin.get('/api/v1/jobs?sort=-created_at').data['jobs']
    assert jobs[-1]['status'] == 'killed'
    assert jobs[-2]['status'] == 'new'


def _update_component(admin, component, data):
    url = '/api/v1/components/%s' % component['id']
    r = admin.put(url, headers={'If-match': component['etag']}, data=data)
    assert r.status_code == 204
    return admin.get(url).data['component']


def test_schedule_job_with_export_control(admin, remoteci_context,
                                          remoteci, topic):
    components = admin.get('/api/v1/topics/%s/components' % topic['id']).data['components']  # noqa
    _update_component(admin, components[0], {'export_control': False})

    data = {'topic_id': topic['id']}
    r = remoteci_context.post('/api/v1/jobs/schedule', data=data)
    assert r.status_code == 412

    components = admin.get('/api/v1/topics/%s/components' % topic['id']).data['components']  # noqa
    _update_component(admin, components[0], {'export_control': True})

    data = {'topic_id': topic['id']}
    r = remoteci_context.post('/api/v1/jobs/schedule', data=data)
    assert r.status_code == 201


def test_schedule_jobs_round_robin_rconfiguration(admin, remoteci_context,
                                                  topic):

    remoteci = remoteci_context.get('/api/v1/identity').data['identity']
    rconfiguration_1 = _create_rconfiguration(
        admin, remoteci['id'], {'name': 'rc1', 'topic_id': topic['id']}
    )
    rconfiguration_2 = _create_rconfiguration(
        admin, remoteci['id'], {'name': 'rc2', 'topic_id': topic['id']}
    )

    data = {'topic_id': topic['id']}
    j1 = remoteci_context.post('/api/v1/jobs/schedule', data=data).data['job']

    data = {'topic_id': topic['id']}
    j2 = remoteci_context.post('/api/v1/jobs/schedule', data=data).data['job']

    list_round_robin = [rconfiguration_1['id'], rconfiguration_2['id']]
    assert j1['rconfiguration_id'] in list_round_robin
    assert j2['rconfiguration_id'] in list_round_robin
    assert j1['rconfiguration_id'] != j2['rconfiguration_id']
