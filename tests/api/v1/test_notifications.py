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


def test_get_emails_from_remoteci(user, remoteci_user_id, app, engine, session):
    r = user.post("/api/v1/remotecis/%s/users" % remoteci_user_id)
    assert r.status_code == 201

    with app.app_context():
        flask.g.db_conn = engine.connect()
        flask.g.session = session
        emails = notifications.get_emails_from_remoteci(remoteci_user_id)
        assert emails == ["user@example.org"]


def test_get_emails_from_remoteci_deleted(user, remoteci_user_id, app, engine, session):
    r = user.post("/api/v1/remotecis/%s/users" % remoteci_user_id)
    assert r.status_code == 201
    r = user.get("/api/v1/remotecis/%s" % remoteci_user_id)
    r = user.delete(
        "/api/v1/remotecis/%s" % remoteci_user_id,
        headers={"If-match": r.data["remoteci"]["etag"]},
    )
    assert r.status_code == 204

    with app.app_context():
        flask.g.db_conn = engine.connect()
        flask.g.session = session
        emails = notifications.get_emails_from_remoteci(remoteci_user_id)
        assert emails == []


@mock.patch("dci.api.v1.notifications.job_dispatcher")
def test_get_job_event_on_job_error(mocked_disp, user, job_user_id):
    # set job to error status
    data = {"job_id": job_user_id, "status": "error"}
    user.post("/api/v1/jobstates", data=data)
    job = user.get(
        "/api/v1/jobs/%s?embed=components,topic,remoteci,results" % job_user_id
    )
    job = job.data["job"]
    email_event = notifications.get_job_event(job, ["user@exameple.org"])
    assert email_event["event"] == "notification"
    assert email_event["emails"] == ["user@exameple.org"]
    assert email_event["job_id"] == job_user_id
    assert email_event["status"] == "error"
    assert email_event["topic_id"] == job["topic_id"]
    assert email_event["topic_name"] == job["topic"]["name"]
    assert email_event["remoteci_id"] == job["remoteci_id"]
    assert email_event["remoteci_name"] == job["remoteci"]["name"]
    assert len(email_event["components"]) == 1
    assert email_event["regressions"] == {}


@mock.patch("dci.api.v1.notifications.job_dispatcher")
def test_get_job_event_on_job_success(mocked_disp, user, job_user_id):
    # set job to error status
    data = {"job_id": job_user_id, "status": "success"}
    user.post("/api/v1/jobstates", data=data)
    job = user.get(
        "/api/v1/jobs/%s?embed=components,topic,remoteci,results" % job_user_id
    )
    job = job.data["job"]
    email_event = notifications.get_job_event(job, ["user@exameple.org"])
    assert email_event is None


def test_format_job_mail_message():
    expected_message = """
You are receiving this email because of the DCI job abc123 for the
topic rhel-7.8 on the Remote CI rhel_labs.

The final status of the job is: failure

The components used are: c_1, c_2


For more information:
https://www.distributed-ci.io/jobs/abc123
"""
    mesg = {
        "job_id": "abc123",
        "topic_name": "rhel-7.8",
        "remoteci_name": "rhel_labs",
        "status": "failure",
        "components": ["c_1", "c_2"],
        "regressions": {},
    }
    assert expected_message == notifications.format_job_mail_message(mesg)


@mock.patch("dci.api.v1.notifications.component_dispatcher")
def test_new_component_created(mocked_disp, admin, topic_user_id):
    _arg = {}

    def side_effect(component):
        _arg.update(component)

    mocked_disp.side_effect = side_effect

    data = {
        "name": "pname",
        "type": "gerrit_review",
        "url": "http://example.com/",
        "topic_id": topic_user_id,
        "state": "active",
    }
    admin.post("/api/v1/components", data=data).data
    mocked_disp.assert_called_once_with(_arg)


def test_delete_a_remoteci_delete_the_associated_subscriptions(
    user, user_id, team_user_id
):
    remoteci = user.post(
        "/api/v1/remotecis",
        data={"name": "My remoteci", "team_id": team_user_id},
    ).data["remoteci"]

    r = user.post("/api/v1/remotecis/%s/users" % remoteci["id"])
    assert r.status_code == 201

    r = user.delete(
        "/api/v1/remotecis/%s" % remoteci["id"],
        headers={"If-match": remoteci["etag"]},
    )
    assert r.status_code == 204

    subscribed_remotecis = user.get("/api/v1/users/%s/remotecis" % user_id).data[
        "remotecis"
    ]
    assert len(subscribed_remotecis) == 0
