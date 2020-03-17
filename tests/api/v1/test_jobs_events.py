# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Red Hat, Inc
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


@mock.patch("dci.api.v1.notifications.dispatcher")
def test_jobs_events_create(mocked_disp, admin, user, job_user_id, reset_job_event):
    data = {'job_id': job_user_id, 'status': 'success', 'comment': 'kikoolol'}
    user.post('/api/v1/jobstates', data=data).data
    j_events = admin.get('/api/v1/jobs_events/0?sort=id')
    job_event = j_events.data['jobs_events'][0]
    assert job_event['job_id'] == job_user_id
    assert job_event['status'] == 'success'
    assert j_events.status_code == 200


@mock.patch("dci.api.v1.notifications.dispatcher")
def test_jobs_events_delete_from_sequence_number(
    mocked_disp, admin, user, job_user_id, reset_job_event
):
    data = {'job_id': job_user_id, 'status': 'success', 'comment': 'kikoolol'}
    user.post('/api/v1/jobstates', data=data).data
    j_events = admin.get('/api/v1/jobs_events/0?sort=id').data
    assert len(j_events['jobs_events']) == 1

    admin.delete('/api/v1/jobs_events/0')

    f_events = admin.get('/api/v1/jobs_events/0').data
    assert len(f_events['jobs_events']) == 0


def test_files_events_user_unauthorized(user):
    j_events = user.get('/api/v1/jobs_events/0')
    assert j_events.status_code == 401


def test_get_jobs_events_sequence(admin):
    sequence = admin.get('/api/v1/jobs_events/sequence')
    assert sequence.status_code == 200
    sequence = sequence.data['sequence']
    assert sequence['sequence'] == 0


def test_put_jobs_events_sequence(admin):
    sequence = admin.get('/api/v1/jobs_events/sequence')
    assert sequence.status_code == 200
    etag = sequence.data['sequence']['etag']
    result = admin.put('/api/v1/jobs_events/sequence',
                       data={'sequence': 1234},
                       headers={'If-match': etag})
    assert result.status_code == 204
    sequence = admin.get('/api/v1/jobs_events/sequence')
    assert sequence.data['sequence']['sequence'] == 1234
