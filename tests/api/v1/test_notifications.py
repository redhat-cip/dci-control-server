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

from __future__ import unicode_literals

from dci.api.v1 import notifications

import flask
import mock


def test_get_emails(user, remoteci_user_id, app, engine):

    r = user.post('/api/v1/remotecis/%s/users' % remoteci_user_id)
    assert r.status_code == 201

    with app.app_context():
        flask.g.db_conn = engine.connect()
        emails = notifications.get_emails(remoteci_user_id)
        assert emails == ['user@example.org']


def test_get_emails_remoteci_deleted(user, remoteci_user_id, app, engine):

    r = user.post('/api/v1/remotecis/%s/users' % remoteci_user_id)
    assert r.status_code == 201
    r = user.get('/api/v1/remotecis/%s' % remoteci_user_id)
    r = user.delete('/api/v1/remotecis/%s' % remoteci_user_id,
                    headers={'If-match': r.data['remoteci']['etag']})
    assert r.status_code == 204

    with app.app_context():
        flask.g.db_conn = engine.connect()
        emails = notifications.get_emails(remoteci_user_id)
        assert emails == []


@mock.patch("dci.api.v1.notifications.dispatcher")
def test_get_email_event_on_job_error(mocked_disp, user, job_user_id):
    # set job to error status
    data = {'job_id': job_user_id, 'status': 'error'}
    user.post('/api/v1/jobstates', data=data)
    job = user.get('/api/v1/jobs/%s?embed=components,topic,remoteci,results' % job_user_id)  # noqa
    job = job.data['job']
    email_event = notifications.get_email_event(job, ['user@exameple.org'])
    assert email_event['event'] == 'notification'
    assert email_event['emails'] == ['user@exameple.org']
    assert email_event['job_id'] == job_user_id
    assert email_event['status'] == 'error'
    assert email_event['topic_id'] == job['topic_id']
    assert email_event['topic_name'] == job['topic']['name']
    assert email_event['remoteci_id'] == job['remoteci_id']
    assert email_event['remoteci_name'] == job['remoteci']['name']
    assert len(email_event['components']) == 3
    assert email_event['regressions'] == {}


@mock.patch("dci.api.v1.notifications.send_events")
def test_dispatcher_no_notification_event(mocked_send_events, user, job_user_id, remoteci_user_id):
    user.post('/api/v1/remotecis/%s/users' % remoteci_user_id)
    # set job to error status
    data = {'job_id': job_user_id, 'status': 'success'}
    user.post('/api/v1/jobstates', data=data)
    for ev in mocked_send_events.call_args_list:
        assert ev.args[0][0]['event'] != 'notification'


@mock.patch("dci.api.v1.notifications.send_events")
def test_dispatcher_notification_event(mocked_send_events, user, job_user_id, remoteci_user_id):
    user.post('/api/v1/remotecis/%s/users' % remoteci_user_id)
    # set job to error status
    data = {'job_id': job_user_id, 'status': 'failure'}
    user.post('/api/v1/jobstates', data=data)
    is_event_notification = False
    for ev in mocked_send_events.call_args_list:
        if ev.args[0][0]['event'] == 'notification':
            is_event_notification = True
    assert is_event_notification


def test_format_mail_message():
    expected_message = """
You are receiving this email because of the DCI job abc123 for the
topic rhel-7.8 on the Remote CI rhel_labs.

The final status of the job is: failure

The components used are: c_1, c_2


For more information:
https://www.distributed-ci.io/jobs/abc123
"""
    mesg = {'job_id': 'abc123',
            'topic_name': 'rhel-7.8',
            'remoteci_name': 'rhel_labs',
            'status': 'failure',
            'components': ['c_1', 'c_2'],
            'regressions': {}
            }
    assert expected_message == notifications.format_mail_message(mesg)
