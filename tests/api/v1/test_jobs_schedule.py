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
import datetime
from mock import patch


def test_schedule_jobs(remoteci_context, rhel_80_topic, rhel_80_component):
    headers = {
        "User-Agent": "python-dciclient",
        "Client-Version": "python-dciclient_0.1.0",
    }
    data = {"topic_id": rhel_80_topic["id"]}
    r = remoteci_context.post("/api/v1/jobs/schedule", headers=headers, data=data)
    assert r.status_code == 201
    job = r.data["job"]
    assert job["topic_id"] == rhel_80_topic["id"]
    assert job["user_agent"] == headers["User-Agent"]
    assert job["client_version"] == headers["Client-Version"]


def test_schedule_jobs_with_components_ids(
    user, remoteci_context, rhel_80_topic, rhel_80_component
):
    components = user.get("/api/v1/topics/%s/components" % rhel_80_topic["id"]).data[
        "components"
    ]
    assert len(components) == 1
    assert components[0]["id"] == rhel_80_component["id"]
    data = {"topic_id": rhel_80_topic["id"], "components_ids": [components[0]["id"]]}
    r = remoteci_context.post("/api/v1/jobs/schedule", data=data)
    assert r.status_code == 201


def test_schedule_jobs_with_previous_job_id(
    remoteci_context, rhel_80_topic, rhel_80_component
):
    r = remoteci_context.post(
        "/api/v1/jobs/schedule", data={"topic_id": rhel_80_topic["id"]}
    )
    assert r.status_code == 201
    job1 = r.data["job"]
    assert job1["topic_id"] == rhel_80_topic["id"]
    r = remoteci_context.post(
        "/api/v1/jobs/schedule",
        data={"topic_id": rhel_80_topic["id"], "previous_job_id": job1["id"]},
    )
    assert r.status_code == 201
    job2 = r.data["job"]
    assert job2["topic_id"] == rhel_80_topic["id"]
    assert job2["previous_job_id"] == job1["id"]


def _update_remoteci(admin, id, etag, data):
    url = "/api/v1/remotecis/%s" % id
    r = admin.put(url, headers={"If-match": etag}, data=data)
    assert r.status_code == 200
    return admin.get(url).data["remoteci"]


def test_schedule_jobs_on_remoteci_inactive(
    admin, remoteci_context, rhel_80_topic, rhel_80_component
):
    remoteci = remoteci_context.get("/api/v1/identity").data["identity"]
    remoteci["etag"] = admin.get("/api/v1/remotecis/%s" % remoteci["id"]).data[
        "remoteci"
    ]["etag"]

    remoteci = _update_remoteci(
        admin, remoteci["id"], remoteci["etag"], {"state": "inactive"}
    )
    data = {"topic_id": rhel_80_topic["id"]}
    r = remoteci_context.post("/api/v1/jobs/schedule", data=data)
    assert r.status_code != 201

    remoteci = _update_remoteci(
        admin, remoteci["id"], remoteci["etag"], {"state": "active"}
    )
    data = {"topic_id": rhel_80_topic["id"]}
    r = remoteci_context.post("/api/v1/jobs/schedule", data=data)
    assert r.status_code == 201


def test_schedule_jobs_on_remoteci_team_inactive(
    admin, remoteci_context, rhel_80_topic, rhel_80_component, team_user_id
):
    team_etag = admin.get("/api/v1/teams/%s" % team_user_id).data["team"]["etag"]
    r = admin.put(
        "/api/v1/teams/%s" % team_user_id,
        headers={"If-match": team_etag},
        data={"state": "inactive"},
    )
    assert r.status_code == 200

    data = {"topic_id": rhel_80_topic["id"]}
    r = remoteci_context.post("/api/v1/jobs/schedule", data=data)
    assert r.status_code == 412

    team_etag = admin.get("/api/v1/teams/%s" % team_user_id).data["team"]["etag"]
    r = admin.put(
        "/api/v1/teams/%s" % team_user_id,
        headers={"If-match": team_etag},
        data={"state": "active"},
    )
    assert r.status_code == 200

    data = {"topic_id": rhel_80_topic["id"]}
    r = remoteci_context.post("/api/v1/jobs/schedule", data=data)
    assert r.status_code == 201


def _update_topic(admin, rhel_80_topic, data):
    url = "/api/v1/topics/%s" % rhel_80_topic["id"]
    r = admin.put(url, headers={"If-match": rhel_80_topic["etag"]}, data=data)
    assert r.status_code == 200
    return admin.get(url).data["topic"]


def test_schedule_jobs_on_topic_inactive(
    admin, remoteci_context, rhel_80_topic, rhel_80_component, team_user_id
):
    admin.post(
        "/api/v1/topics/%s/teams" % rhel_80_topic["id"], data={"team_id": team_user_id}
    )
    rhel_80_topic = _update_topic(admin, rhel_80_topic, {"state": "inactive"})
    data = {"topic_id": rhel_80_topic["id"]}
    r = remoteci_context.post("/api/v1/jobs/schedule", data=data)
    assert r.status_code == 412

    rhel_80_topic = _update_topic(admin, rhel_80_topic, {"state": "active"})
    data = {"topic_id": rhel_80_topic["id"]}
    r = remoteci_context.post("/api/v1/jobs/schedule", data=data)
    assert r.status_code == 201


def test_schedule_jobs_kills_jobs_older_than_one_day(
    admin, remoteci_context, rhel_80_topic, rhel_80_component
):
    data = {"topic_id": rhel_80_topic["id"]}
    fixed_now = datetime.datetime(2019, 1, 12, 13, 42, 20, 111136)
    with patch("dci.api.v1.jobs.get_utc_now", return_value=fixed_now):
        r = remoteci_context.post("/api/v1/jobs/schedule", data=data)
        assert r.status_code == 201

    r = remoteci_context.post("/api/v1/jobs/schedule", data=data)
    assert r.status_code == 201

    r = remoteci_context.post("/api/v1/jobs/schedule", data=data)
    assert r.status_code == 201
    jobs = admin.get("/api/v1/jobs?sort=-created_at").data["jobs"]
    assert jobs[-1]["status"] == "killed"
    assert jobs[-2]["status"] == "new"
    assert jobs[-3]["status"] == "new"
