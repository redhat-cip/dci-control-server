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


def test_get_emails_from_remoteci(
    client_user1, team1_remoteci_id, app, engine, session
):
    r = client_user1.post("/api/v1/remotecis/%s/users" % team1_remoteci_id)
    assert r.status_code == 201

    with app.app_context():
        flask.g.db_conn = engine.connect()
        flask.g.session = session
        emails = notifications.get_emails_from_remoteci(team1_remoteci_id)
        assert emails == ["user1@example.org"]


def test_get_emails_from_remoteci_deleted(
    client_user1, team1_remoteci_id, app, engine, session
):
    r = client_user1.post("/api/v1/remotecis/%s/users" % team1_remoteci_id)
    assert r.status_code == 201
    r = client_user1.get("/api/v1/remotecis/%s" % team1_remoteci_id)
    r = client_user1.delete(
        "/api/v1/remotecis/%s" % team1_remoteci_id,
        headers={"If-match": r.data["remoteci"]["etag"]},
    )
    assert r.status_code == 204

    with app.app_context():
        flask.g.db_conn = engine.connect()
        flask.g.session = session
        emails = notifications.get_emails_from_remoteci(team1_remoteci_id)
        assert emails == []


@mock.patch("dci.api.v1.notifications.job_dispatcher")
def test_get_job_event_on_job_error(mocked_disp, client_user1, team1_job_id):
    # set job to error status
    data = {"job_id": team1_job_id, "status": "error"}
    client_user1.post("/api/v1/jobstates", data=data)
    job = client_user1.get(
        "/api/v1/jobs/%s?embed=components,topic,remoteci,results" % team1_job_id
    )
    job = job.data["job"]
    email_event = notifications.get_job_event(job, ["user1@example.org"])
    assert email_event["event"] == "notification"
    assert email_event["emails"] == ["user1@example.org"]
    assert email_event["job_id"] == team1_job_id
    assert email_event["status"] == "error"
    assert email_event["topic_id"] == job["topic_id"]
    assert email_event["topic_name"] == job["topic"]["name"]
    assert email_event["remoteci_id"] == job["remoteci_id"]
    assert email_event["remoteci_name"] == job["remoteci"]["name"]
    assert len(email_event["components"]) == 1
    assert email_event["regressions"] == {}


@mock.patch("dci.api.v1.notifications.job_dispatcher")
def test_get_job_event_on_job_success(mocked_disp, client_user1, team1_job_id):
    # set job to error status
    data = {"job_id": team1_job_id, "status": "success"}
    client_user1.post("/api/v1/jobstates", data=data)
    job = client_user1.get(
        "/api/v1/jobs/%s?embed=components,topic,remoteci,results" % team1_job_id
    )
    job = job.data["job"]
    email_event = notifications.get_job_event(job, ["user1@example.org"])
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
def test_new_component_created(mocked_disp, client_admin, rhel_80_topic_id):
    _arg = {}

    def side_effect(component):
        _arg.update(component)

    mocked_disp.side_effect = side_effect

    data = {
        "name": "pname",
        "type": "gerrit_review",
        "url": "http://example.com/",
        "topic_id": rhel_80_topic_id,
        "state": "active",
    }
    client_admin.post("/api/v1/components", data=data).data
    mocked_disp.assert_called_once_with(_arg)


def test_delete_a_remoteci_delete_the_associated_subscriptions(
    client_user1, user1_id, team1_id
):
    remoteci = client_user1.post(
        "/api/v1/remotecis",
        data={"name": "My remoteci", "team_id": team1_id},
    ).data["remoteci"]

    r = client_user1.post("/api/v1/remotecis/%s/users" % remoteci["id"])
    assert r.status_code == 201

    r = client_user1.delete(
        "/api/v1/remotecis/%s" % remoteci["id"],
        headers={"If-match": remoteci["etag"]},
    )
    assert r.status_code == 204

    subscribed_remotecis = client_user1.get(
        "/api/v1/users/%s/remotecis" % user1_id
    ).data["remotecis"]
    assert len(subscribed_remotecis) == 0
