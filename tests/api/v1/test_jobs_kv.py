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


def test_add_kv_to_job(hmac_client_team1, rhel_80_topic_id, rhel_80_component_id):
    data = {
        "components": [rhel_80_component_id],
        "topic_id": rhel_80_topic_id,
        "name": "my-job-name",
    }
    job = hmac_client_team1.post("/api/v1/jobs", data=data)
    job_id = job.data["job"]["id"]

    job = hmac_client_team1.get("/api/v1/jobs/%s" % job_id)
    job = job.data["job"]
    assert job["keys_values"] == []

    r = hmac_client_team1.post(
        "/api/v1/jobs/%s/kv" % job_id,
        data={"key": "mykey", "value": 123},
    )
    r.status_code == 201

    job = hmac_client_team1.get("/api/v1/jobs/%s" % job_id)
    assert job.data["job"]["keys_values"][0]["job_id"] == job_id
    assert job.data["job"]["keys_values"][0]["key"] == "mykey"
    assert job.data["job"]["keys_values"][0]["value"] == 123

    # fail on duplicated key
    r = hmac_client_team1.post(
        "/api/v1/jobs/%s/kv" % job_id,
        data={"key": "mykey", "value": 1234},
    )
    r.status_code == 409


def test_delete_from_job(hmac_client_team1, rhel_80_topic_id, rhel_80_component_id):
    data = {
        "components": [rhel_80_component_id],
        "topic_id": rhel_80_topic_id,
        "name": "my-job-name",
    }
    job = hmac_client_team1.post("/api/v1/jobs", data=data)
    job_id = job.data["job"]["id"]

    job = hmac_client_team1.get("/api/v1/jobs/%s" % job_id)
    job = job.data["job"]
    assert job["keys_values"] == []

    r = hmac_client_team1.post(
        "/api/v1/jobs/%s/kv" % job_id,
        data={"key": "mykey", "value": 123.123},
    )
    r.status_code == 201

    job = hmac_client_team1.get("/api/v1/jobs/%s" % job_id)
    assert job.data["job"]["keys_values"][0]["job_id"] == job_id
    assert job.data["job"]["keys_values"][0]["key"] == "mykey"
    assert job.data["job"]["keys_values"][0]["value"] == 123.123

    r = hmac_client_team1.delete(
        "/api/v1/jobs/%s/kv" % job_id,
        data={"key": "mykey"},
    )
    r.status_code == 204

    job = hmac_client_team1.get("/api/v1/jobs/%s" % job_id)
    job = job.data["job"]
    assert job["keys_values"] == []


def test_job_updated_when_kv_added_deleted(hmac_client_team1, team1_job_id):
    job = hmac_client_team1.get("/api/v1/jobs/%s" % team1_job_id).data["job"]
    job_updated_at = job["updated_at"]

    r = hmac_client_team1.post(
        "/api/v1/jobs/%s/kv" % team1_job_id,
        data={"key": "mykey", "value": 123.123},
    )
    r.status_code == 201

    job = hmac_client_team1.get("/api/v1/jobs/%s" % team1_job_id).data["job"]
    assert job["updated_at"] != job_updated_at

    job_updated_at = job["updated_at"]
    r = hmac_client_team1.delete(
        "/api/v1/jobs/%s/kv" % team1_job_id,
        data={"key": "mykey"},
    )
    r.status_code == 204

    job = hmac_client_team1.get("/api/v1/jobs/%s" % team1_job_id).data["job"]
    assert job["updated_at"] != job_updated_at
