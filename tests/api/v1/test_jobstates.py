# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2023 Red Hat, Inc
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


def test_create_jobstates(client_user1, team1_job_id):
    data = {"job_id": team1_job_id, "status": "running", "comment": "kikoolol"}

    with mock.patch("dci.api.v1.notifications") as mocked_notif:
        js = client_user1.post("/api/v1/jobstates", data=data).data
        assert not mocked_notif.job_dispatcher.called
    js_id = js["jobstate"]["id"]

    js = client_user1.get("/api/v1/jobstates/%s" % js_id).data
    job = client_user1.get("/api/v1/jobs/%s" % team1_job_id).data

    assert js["jobstate"]["comment"] == "kikoolol"
    assert job["job"]["status"] == "running"


@mock.patch("dci.api.v1.jobstates.notifications.job_dispatcher")
def test_create_jobstates_failure(mocked_disp, client_user1, team1_job_id):
    data = {"job_id": team1_job_id, "status": "failure"}
    client_user1.post("/api/v1/jobstates", data=data)
    # Notification should be sent just one time
    client_user1.post("/api/v1/jobstates", data=data)
    mocked_disp.assert_called_once()

    job = client_user1.get("/api/v1/jobs/%s" % team1_job_id).data
    assert job["job"]["status"] == "failure"


@mock.patch("dci.api.v1.notifications.job_dispatcher")
def test_create_jobstates_notification(mocked_disp, client_user1, team1_job_id):
    data = {"job_id": team1_job_id, "status": "failure"}

    client_user1.post("/api/v1/jobstates", data=data)
    events, _ = mocked_disp.call_args
    event = events[0]
    assert "components" in event
    assert "topic" in event
    assert "remoteci" in event
    assert "results" in event


@mock.patch("dci.api.v1.notifications.job_dispatcher")
def test_create_final_job_status_umb_notification(
    mocked_disp, client_user1, team1_job_id
):
    data = {"job_id": team1_job_id, "status": "success"}
    client_user1.post("/api/v1/jobstates", data=data)
    events, _ = mocked_disp.call_args
    event = events[0]
    assert str(event["id"]) == team1_job_id


@mock.patch("dci.api.v1.notifications.job_dispatcher")
def test_create_jobstates_new_to_failure(mocked_disp, client_user1, team1_job_id):
    data = {"job_id": team1_job_id, "status": "new"}
    js = client_user1.post("/api/v1/jobstates", data=data).data
    assert js["jobstate"]["status"] == "new"
    data = {"job_id": team1_job_id, "status": "failure"}
    js = client_user1.post("/api/v1/jobstates", data=data).data
    js = client_user1.get("/api/v1/jobstates/%s" % js["jobstate"]["id"]).data
    assert js["jobstate"]["status"] == "error"


@mock.patch("dci.api.v1.notifications.job_dispatcher")
def test_create_jobstates_error(mocked_disp, client_user1, team1_job_id):
    data = {"job_id": team1_job_id, "status": "error"}

    js = client_user1.post("/api/v1/jobstates", data=data).data
    js = client_user1.get("/api/v1/jobstates/%s" % js["jobstate"]["id"]).data
    assert js["jobstate"]["status"] == "error"


def test_create_jobstates_empty_comment(client_user1, team1_job_id):
    data = {"job_id": team1_job_id, "status": "running"}

    js = client_user1.post("/api/v1/jobstates", data=data).data
    assert js["jobstate"]["comment"] is None

    js = client_user1.get("/api/v1/jobstates/%s" % js["jobstate"]["id"]).data
    assert js["jobstate"]["comment"] is None


def test_get_jobstate_by_id(client_user1, team1_job_id):
    js = client_user1.post(
        "/api/v1/jobstates",
        data={"job_id": team1_job_id, "comment": "kikoolol", "status": "running"},
    ).data
    js_id = js["jobstate"]["id"]

    # get by uuid
    created_js = client_user1.get("/api/v1/jobstates/%s" % js_id)
    assert created_js.status_code == 200
    assert created_js.data["jobstate"]["comment"] == "kikoolol"
    assert created_js.data["jobstate"]["status"] == "running"


def test_get_jobstate_not_found(client_user1):
    result = client_user1.get("/api/v1/jobstates/%s" % uuid.uuid4())
    assert result.status_code == 404


def test_get_jobstate_with_embed(client_user1, team1_job_id):
    js = client_user1.post(
        "/api/v1/jobstates",
        data={"job_id": team1_job_id, "comment": "kikoolol", "status": "running"},
    ).data
    js_id = js["jobstate"]["id"]

    # verify embed
    js_embed = client_user1.get("/api/v1/jobstates/%s?embed=files,job" % js_id)
    assert js_embed.status_code == 200


@mock.patch("dci.api.v1.notifications.job_dispatcher")
def test_delete_jobstate_by_id(mocked_disp, client_user1, team1_job_id):
    js = client_user1.post(
        "/api/v1/jobstates",
        data={"job_id": team1_job_id, "comment": "kikoolol", "status": "running"},
    )
    js_id = js.data["jobstate"]["id"]

    url = "/api/v1/jobstates/%s" % js_id

    created_js = client_user1.get(url)
    assert created_js.status_code == 200

    deleted_js = client_user1.delete(url)
    assert deleted_js.status_code == 204

    gjs = client_user1.get(url)
    assert gjs.status_code == 404


# Tests for the isolation


@mock.patch("dci.api.v1.notifications.job_dispatcher")
def test_create_jobstate_as_user(mocked_disp, client_user1, team1_job_id):
    jobstate = client_user1.post(
        "/api/v1/jobstates",
        data={"job_id": team1_job_id, "comment": "kikoolol", "status": "running"},
    )
    assert jobstate.status_code == 201

    jobstate_id = jobstate.data["jobstate"]["id"]
    jobstate = client_user1.get("/api/v1/jobstates/%s" % jobstate_id)
    assert jobstate.status_code == 200
    assert jobstate.data["jobstate"]["job_id"] == team1_job_id


@mock.patch("dci.api.v1.notifications.job_dispatcher")
def test_get_jobstate_as_user(mocked_disp, client_user1, team1_jobstate, team1_job_id):
    # jobstate = user.get('/api/v1/jobstates/%s' % jobstate_id)
    # assert jobstate.status_code == 404

    jobstate = client_user1.post(
        "/api/v1/jobstates",
        data={"job_id": team1_job_id, "comment": "kikoolol", "status": "running"},
    ).data
    jobstate_id = jobstate["jobstate"]["id"]
    jobstate = client_user1.get("/api/v1/jobstates/%s" % jobstate_id)
    assert jobstate.status_code == 200


@mock.patch("dci.api.v1.notifications.job_dispatcher")
def test_delete_jobstate_as_user(mocked_disp, client_user1, team1_job_id):
    js_user = client_user1.post(
        "/api/v1/jobstates",
        data={"job_id": team1_job_id, "comment": "kikoolol", "status": "running"},
    )
    js_user_id = js_user.data["jobstate"]["id"]

    jobstate_delete = client_user1.delete("/api/v1/jobstates/%s" % js_user_id)
    assert jobstate_delete.status_code == 204

    # jobstate_delete = user.delete('/api/v1/jobstates/%s' % jobstate_id)
    # assert jobstate_delete.status_code == 401
