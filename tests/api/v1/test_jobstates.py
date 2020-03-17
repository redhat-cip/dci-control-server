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

import mock
import uuid


def test_create_jobstates(user, job_user_id):
    data = {'job_id': job_user_id, 'status': 'running', 'comment': 'kikoolol'}

    with mock.patch('dci.api.v1.notifications') as mocked_notif:
        js = user.post('/api/v1/jobstates', data=data).data
        assert not mocked_notif.displatcher.called
    js_id = js['jobstate']['id']

    js = user.get('/api/v1/jobstates/%s' % js_id).data
    job = user.get('/api/v1/jobs/%s' % job_user_id).data

    assert js['jobstate']['comment'] == 'kikoolol'
    assert job['job']['status'] == 'running'


def test_create_jobstates_failure(user, job_user_id):
    data = {'job_id': job_user_id, 'status': 'failure'}

    with mock.patch('dci.api.v1.notifications.dispatcher') as mocked_disp:
        user.post('/api/v1/jobstates', data=data)
        # Notification should be sent just one time
        user.post('/api/v1/jobstates', data=data)
        assert mocked_disp.called_once()

    job = user.get('/api/v1/jobs/%s' % job_user_id).data
    assert job['job']['status'] == 'failure'


def test_create_jobstates_notification(user, job_user_id):
    data = {'job_id': job_user_id, 'status': 'failure'}

    with mock.patch('dci.api.v1.notifications.dispatcher') as mocked_disp:
        user.post('/api/v1/jobstates', data=data)
        events, _ = mocked_disp.call_args
        event = events[0]
        assert 'components' in event
        assert 'topic' in event
        assert 'remoteci' in event
        assert 'results' in event


def test_create_final_job_status_umb_notification(user, job_user_id):
    data = {'job_id': job_user_id, 'status': 'success'}

    with mock.patch('dci.api.v1.notifications.dispatcher') as mocked_disp:
        user.post('/api/v1/jobstates', data=data)
        events, _ = mocked_disp.call_args
        event = events[0]
        assert str(event['id']) == job_user_id


def test_create_jobstates_new_to_failure(user, job_user_id):
    data = {'job_id': job_user_id, 'status': 'new'}
    js = user.post('/api/v1/jobstates', data=data).data
    assert js['jobstate']['status'] == 'new'
    data = {'job_id': job_user_id, 'status': 'failure'}
    js = user.post('/api/v1/jobstates', data=data).data
    js = user.get('/api/v1/jobstates/%s' % js['jobstate']['id']).data
    assert js['jobstate']['status'] == 'error'


def test_create_jobstates_error(user, job_user_id):
    data = {'job_id': job_user_id, 'status': 'error'}

    js = user.post('/api/v1/jobstates', data=data).data
    js = user.get('/api/v1/jobstates/%s' % js['jobstate']['id']).data
    assert js['jobstate']['status'] == 'error'


def test_create_jobstates_empty_comment(user, job_user_id):
    data = {'job_id': job_user_id, 'status': 'running'}

    js = user.post('/api/v1/jobstates', data=data).data
    assert js['jobstate']['comment'] is None

    js = user.get('/api/v1/jobstates/%s' % js['jobstate']['id']).data
    assert js['jobstate']['comment'] is None


def test_get_jobstate_by_id(user, job_user_id):
    js = user.post('/api/v1/jobstates',
                   data={'job_id': job_user_id,
                         'comment': 'kikoolol',
                         'status': 'running'}).data
    js_id = js['jobstate']['id']

    # get by uuid
    created_js = user.get('/api/v1/jobstates/%s' % js_id)
    assert created_js.status_code == 200
    assert created_js.data['jobstate']['comment'] == 'kikoolol'
    assert created_js.data['jobstate']['status'] == 'running'


def test_get_jobstate_not_found(user):
    result = user.get('/api/v1/jobstates/%s' % uuid.uuid4())
    assert result.status_code == 404


def test_get_jobstate_with_embed(user, job_user_id):
    js = user.post('/api/v1/jobstates',
                   data={'job_id': job_user_id,
                         'comment': 'kikoolol',
                         'status': 'running'}).data
    js_id = js['jobstate']['id']

    # verify embed
    js_embed = user.get('/api/v1/jobstates/%s?embed=files,job' % js_id)
    assert js_embed.status_code == 200


def test_get_jobstate_with_embed_not_valid(user, job_user_id):
    js = user.post('/api/v1/jobstates',
                   data={'job_id': job_user_id,
                         'comment': 'kikoolol',
                         'status': 'running'}).data
    js = user.get('/api/v1/jobstates/%s?embed=mdr' % js['jobstate']['id'])
    assert js.status_code == 400


def test_delete_jobstate_by_id(user, job_user_id):
    js = user.post('/api/v1/jobstates',
                   data={'job_id': job_user_id,
                         'comment': 'kikoolol',
                         'status': 'running'})
    js_id = js.data['jobstate']['id']

    url = '/api/v1/jobstates/%s' % js_id

    created_js = user.get(url)
    assert created_js.status_code == 200

    deleted_js = user.delete(url)
    assert deleted_js.status_code == 204

    gjs = user.get(url)
    assert gjs.status_code == 404

# Tests for the isolation


def test_create_jobstate_as_user(user, job_user_id):
    jobstate = user.post('/api/v1/jobstates',
                         data={'job_id': job_user_id,
                               'comment': 'kikoolol',
                               'status': 'running'})
    assert jobstate.status_code == 201

    jobstate_id = jobstate.data['jobstate']['id']
    jobstate = user.get('/api/v1/jobstates/%s' % jobstate_id)
    assert jobstate.status_code == 200
    assert jobstate.data['jobstate']['job_id'] == job_user_id


def test_get_jobstate_as_user(user, jobstate_user_id, job_user_id):
    # jobstate = user.get('/api/v1/jobstates/%s' % jobstate_id)
    # assert jobstate.status_code == 404

    jobstate = user.post('/api/v1/jobstates',
                         data={'job_id': job_user_id,
                               'comment': 'kikoolol',
                               'status': 'running'}).data
    jobstate_id = jobstate['jobstate']['id']
    jobstate = user.get('/api/v1/jobstates/%s' % jobstate_id)
    assert jobstate.status_code == 200


def test_delete_jobstate_as_user(user, job_user_id):
    js_user = user.post('/api/v1/jobstates',
                        data={'job_id': job_user_id,
                              'comment': 'kikoolol',
                              'status': 'running'})
    js_user_id = js_user.data['jobstate']['id']

    jobstate_delete = user.delete('/api/v1/jobstates/%s' % js_user_id)
    assert jobstate_delete.status_code == 204

    # jobstate_delete = user.delete('/api/v1/jobstates/%s' % jobstate_id)
    # assert jobstate_delete.status_code == 401
