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

import uuid


def test_schedule_jobs(admin, team_id, remoteci_id,
                       topic_id, components_ids):
    headers = {
        'User-Agent': 'thisismyuseragent',
        'Client-Version': 'python-dciclient_0.1.0'
    }
    job = admin.post('/api/v1/jobs/schedule', headers=headers,
                     data={'remoteci_id': remoteci_id,
                           'topic_id': topic_id})

    assert job.status_code == 201
    job = job.data['job']
    assert job['topic_id'] == topic_id
    assert job['team_id'] == team_id
    assert job['remoteci_id'] == remoteci_id
    assert job['user_agent'] == headers['User-Agent']
    assert job['client_version'] == headers['Client-Version']
    assert job['allow_upgrade_job'] is True
    assert job['rconfiguration_id'] is None


def _create_components(user, topic_id, component_types):
    component_ids = []
    for ct in component_types:
        data = {'topic_id': topic_id,
                'name': 'name-' + str(uuid.uuid4()),
                'type': ct,
                'export_control': True}
        cmpt = user.post('/api/v1/components', data=data).data
        component_ids.append(str(cmpt['component']['id']))
    return component_ids


def test_schedule_jobs_with_new_topic(admin, user, remoteci_user_id,
                                      team_user_id, product):

    # create a new topic and schedule a new job
    data = {'name': 'new_topic', 'product_id': product['id'],
            'component_types': ['type_1', 'type_2']}
    pt = admin.post('/api/v1/topics', data=data).data
    new_topic_id = pt['topic']['id']
    _create_components(admin, new_topic_id, ['type_1', 'type_2'])

    # The team does not belongs to topic yet
    job_scheduled = user.post('/api/v1/jobs/schedule',
                              data={'remoteci_id': remoteci_user_id,
                                    'topic_id': new_topic_id})
    assert job_scheduled.status_code == 412

    # Add the team to the topic
    admin.post('/api/v1/topics/%s/teams' % new_topic_id,
               data={'team_id': team_user_id})

    # now schedule a job on that new topic
    job_scheduled = admin.post('/api/v1/jobs/schedule',
                               data={'remoteci_id': remoteci_user_id,
                                     'topic_id': new_topic_id})
    assert job_scheduled.status_code == 201
    job = job_scheduled.data['job']
    assert job['topic_id'] == new_topic_id


def test_schedule_job_with_remoteci_deactivated(admin, remoteci_id, topic_id):
    admin.put('/api/v1/remotecis/%s' % remoteci_id, data={'active': False})
    job_scheduled = admin.post('/api/v1/jobs/schedule',
                               data={'remoteci_id': remoteci_id,
                                     'topic_id': topic_id})
    assert job_scheduled.status_code == 412


def test_schedule_jobs_topic_not_active(admin, remoteci_id, topic_id):
    """No active topic

    Inactive topic, scheduler should return::

        No jobs available for run (412).
    """
    tp = admin.get('/api/v1/topics/%s' % topic_id).data
    ptp = admin.put('/api/v1/topics/%s' % topic_id,
                    data={'state': 'inactive'},
                    headers={'If-match': tp['topic']['etag']})
    assert ptp.status_code == 204
    job = admin.post('/api/v1/jobs/schedule',
                     data={'remoteci_id': remoteci_id,
                           'topic_id': topic_id})
    assert job.status_code == 412


def test_schedule_kill_old_jobs(admin, jobdefinition_factory, remoteci_id,
                                topic_id):
    """when a job is scheduled for a remoteci, the old ones must be killed."""
    jobdefinition_factory('1st')
    jobdefinition_factory('2nd')
    jobdefinition_factory('3rd')

    r = admin.post('/api/v1/jobs/schedule',
                   data={'remoteci_id': remoteci_id,
                         'topic_id': topic_id})
    assert r.status_code == 201
    r = admin.post('/api/v1/jobs/schedule',
                   data={'remoteci_id': remoteci_id,
                         'topic_id': topic_id})
    assert r.status_code == 201

    # all the jobs but the last one should be killed
    jobs = admin.get('/api/v1/jobs?sort=created_at').data
    assert jobs['jobs'][0]['status'] == 'killed'
    assert jobs['jobs'][1]['status'] == 'new'


def test_schedule_give_latest_components(admin, jobdefinition_factory,
                                         remoteci_id, topic_id):
    """The scheduled job should come with the last components."""
    def components_from_job():
        jobdefinition_factory('1st')
        r = admin.post('/api/v1/jobs/schedule',
                       data={'remoteci_id': remoteci_id,
                             'topic_id': topic_id})
        job_id = r.data['job']['id']
        component_url = '/api/v1/jobs/{job_id}/components'
        r = admin.get(component_url.format(job_id=job_id))
        return r.data['components']

    c1 = components_from_job()
    c2 = components_from_job()
    assert set([i['type'] for i in c1]) == set([i['type'] for i in c2])
    assert c1[0]['id'] != c2[0]['id']


def test_schedule_job_with_export_control(admin, remoteci_id, team_admin_id,
                                          product):
    # create a new topic and schedule a new job
    data_topic = {'name': 'new_topic', 'product_id': product['id'],
                  'component_types': ['type_1', 'type_2']}
    pt = admin.post('/api/v1/topics', data=data_topic).data
    new_topic_id = pt['topic']['id']

    # The team does not belongs to topic yet
    job_scheduled = admin.post('/api/v1/jobs/schedule',
                               data={'remoteci_id': remoteci_id,
                                     'topic_id': new_topic_id})
    assert job_scheduled.status_code == 412

    # Add the team to the topic
    admin.post('/api/v1/topics/%s/teams' % new_topic_id,
               data={'team_id': team_admin_id})

    # There is no jobdefinition for this topic yet
    job_scheduled = admin.post('/api/v1/jobs/schedule',
                               data={'remoteci_id': remoteci_id,
                                     'topic_id': new_topic_id})
    assert job_scheduled.status_code == 412

    # Create a jobdefinition for this topic with two components:
    # - the first one is exported
    # - the second one is NOT exported
    data_cmpt_1 = {'topic_id': new_topic_id, 'name': 'name-ct',
                   'type': 'type_1', 'export_control': True}
    cmpt_1 = admin.post('/api/v1/components', data=data_cmpt_1).data

    data_cmpt_2 = {'topic_id': new_topic_id, 'name': 'name-ct2',
                   'type': 'type_2', 'export_control': False}
    cmpt_2 = admin.post('/api/v1/components', data=data_cmpt_2).data

    data = {'name': 'pname', 'topic_id': new_topic_id,
            'component_types': ['type_1', 'type_2']}
    jd = admin.post('/api/v1/jobdefinitions', data=data).data
    jd_id = jd['jobdefinition']['id']

    data = {'component_id': cmpt_1['component']['id']}
    admin.post('/api/v1/jobdefinitions/%s/components' % jd_id, data=data)

    data = {'component_id': cmpt_2['component']['id']}
    admin.post('/api/v1/jobdefinitions/%s/components' % jd_id, data=data)

    # now schedule a job
    job_scheduled = admin.post('/api/v1/jobs/schedule',
                               data={'remoteci_id': remoteci_id,
                                     'topic_id': new_topic_id})
    assert job_scheduled.status_code == 412

    # Add an exported component of type_2
    data_cmpt_3 = {'topic_id': new_topic_id, 'name': 'name-ct3',
                   'type': 'type_2', 'export_control': True}
    admin.post('/api/v1/components', data=data_cmpt_3).data

    job_scheduled = admin.post('/api/v1/jobs/schedule',
                               data={'remoteci_id': remoteci_id,
                                     'topic_id': new_topic_id})
    assert job_scheduled.status_code == 201


def test_schedule_jobs_with_rconfiguration(admin, remoteci_id, topic_id,
                                           jobdefinition_id):

    rconfiguration = admin.post('/api/v1/remotecis/%s/rconfigurations' % remoteci_id,  # noqa
                                data={'name': 'rconfig1',
                                      'topic_id': topic_id})
    rconfiguration_id = rconfiguration.data['rconfiguration']['id']

    headers = {
        'User-Agent': 'thisismyuseragent',
        'Client-Version': 'python-dciclient_0.1.0'
    }
    job = admin.post('/api/v1/jobs/schedule', headers=headers,
                     data={'remoteci_id': remoteci_id,
                           'topic_id': topic_id})
    assert job.status_code == 201
    job = job.data
    assert job['job']['rconfiguration_id'] == rconfiguration_id


def test_schedule_jobs_round_robin_rconfiguration(admin, remoteci_id, topic_id,
                                                  components_ids,
                                                  topic_user_id):

    rconfiguration_1 = admin.post('/api/v1/remotecis/%s/rconfigurations' % remoteci_id,  # noqa
                                data={'name': 'rconfig1',
                                      'topic_id': topic_id})
    rconfiguration_id_1 = rconfiguration_1.data['rconfiguration']['id']

    rconfiguration_2 = admin.post('/api/v1/remotecis/%s/rconfigurations' % remoteci_id,  # noqa
                                  data={'name': 'rconfig2',
                                        'topic_id': topic_id})
    rconfiguration_id_2 = rconfiguration_2.data['rconfiguration']['id']

    rconfiguration_3 = admin.post('/api/v1/remotecis/%s/rconfigurations' % remoteci_id,  # noqa
                                  data={'name': 'rconfig3',
                                        'topic_id': topic_user_id})
    assert rconfiguration_3.status_code == 201

    headers = {
        'User-Agent': 'thisismyuseragent',
        'Client-Version': 'python-dciclient_0.1.0'
    }

    # check round robin
    list_round_robin = [rconfiguration_id_1, rconfiguration_id_2]
    # get the first rconfiguration id
    job = admin.post('/api/v1/jobs/schedule', headers=headers,
                     data={'remoteci_id': remoteci_id,
                           'topic_id': topic_id})
    assert job.status_code == 201
    job = job.data
    # if its the first rconfiguration then inverse list_round_robin
    if job['job']['rconfiguration_id'] == rconfiguration_id_1:
        list_round_robin = [rconfiguration_id_2, rconfiguration_id_1]

    for i in list_round_robin:
        job = admin.post('/api/v1/jobs/schedule', headers=headers,
                         data={'remoteci_id': remoteci_id,
                               'topic_id': topic_id})
        assert job.status_code == 201
        job = job.data
        assert job['job']['rconfiguration_id'] == i


def test_schedule_jobs_with_rconfiguration_and_component_types(
    admin, remoteci_id, topic_id, jobdefinition_id):  # noqa

    rconfiguration = admin.post('/api/v1/remotecis/%s/rconfigurations' % remoteci_id,  # noqa
                                data={'name': 'rconfig1',
                                      'topic_id': topic_id,
                                      'component_types': ['type_1', 'type_2']})
    rconfiguration_id = rconfiguration.data['rconfiguration']['id']

    headers = {
        'User-Agent': 'thisismyuseragent',
        'Client-Version': 'python-dciclient_0.1.0'
    }
    job = admin.post('/api/v1/jobs/schedule', headers=headers,
                     data={'remoteci_id': remoteci_id,
                           'topic_id': topic_id})
    assert job.status_code == 201
    job = job.data
    assert job['job']['rconfiguration_id'] == rconfiguration_id

    gcomponents = admin.get('/api/v1/jobs/%s/components' % job['job']['id']).data  # noqa

    assert len(gcomponents['components']) == 2


def test_schedule_jobs_with_components_ids(admin, user, remoteci_user_id,
                                           topic_user_id,
                                           jobdefinition_user_id):
    c_ids = _create_components(admin, topic_user_id,
                               ['type_1', 'type_2', 'type_3'])
    headers = {
        'User-Agent': 'thisismyuseragent',
        'Client-Version': 'python-dciclient_0.1.0'
    }
    job = user.post('/api/v1/jobs/schedule', headers=headers,
                    data={'remoteci_id': remoteci_user_id,
                          'topic_id': topic_user_id,
                          'components_ids': c_ids}).data

    gcomponents = user.get('/api/v1/jobs/%s/components' % job['job']['id']).data  # noqa
    gcomponents_ids = [g['id'] for g in gcomponents['components']]
    assert set(gcomponents_ids) == set(c_ids)


def test_schedule_jobs_with_bad_components_ids(admin, user, remoteci_user_id,
                                               topic_user_id,
                                               jobdefinition_user_id):
    c_ids = _create_components(admin, topic_user_id,
                               ['type_1', 'type_2', 'type_3'])
    headers = {
        'User-Agent': 'thisismyuseragent',
        'Client-Version': 'python-dciclient_0.1.0'
    }
    # missing one component
    job = user.post('/api/v1/jobs/schedule', headers=headers,
                    data={'remoteci_id': remoteci_user_id,
                          'topic_id': topic_user_id,
                          'components_ids': c_ids[0:1]})
    assert job.status_code == 412

    # duplicate components
    job = user.post('/api/v1/jobs/schedule', headers=headers,
                    data={'remoteci_id': remoteci_user_id,
                          'topic_id': topic_user_id,
                          'components_ids': [c_ids[0], c_ids[1], c_ids[1]]})
    assert job.status_code == 412
