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


def test_add_kv_to_job(remoteci_context, components_user_ids, topic_user_id):
    data = {
        "components": components_user_ids,
        "topic_id": topic_user_id,
        "name": "my-job-name",
    }
    job = remoteci_context.post("/api/v1/jobs", data=data)
    job_id = job.data["job"]["id"]

    job = remoteci_context.get("/api/v1/jobs/%s" % job_id)
    job = job.data["job"]
    assert job["keys_values"] == []

    r = remoteci_context.post(
        "/api/v1/jobs/%s/kv" % job_id,
        data={"key": "mykey", "value": 123},
    )
    r.status_code == 201

    job = remoteci_context.get("/api/v1/jobs/%s" % job_id)
    assert job.data["job"]["keys_values"][0]["job_id"] == job_id
    assert job.data["job"]["keys_values"][0]["key"] == "mykey"
    assert job.data["job"]["keys_values"][0]["value"] == 123

    # fail on duplicated key
    r = remoteci_context.post(
        "/api/v1/jobs/%s/kv" % job_id,
        data={"key": "mykey", "value": 1234},
    )
    r.status_code == 409


def test_delete_from_job(remoteci_context, components_user_ids, topic_user_id):
    data = {
        "components": components_user_ids,
        "topic_id": topic_user_id,
        "name": "my-job-name",
    }
    job = remoteci_context.post("/api/v1/jobs", data=data)
    job_id = job.data["job"]["id"]

    job = remoteci_context.get("/api/v1/jobs/%s" % job_id)
    job = job.data["job"]
    assert job["keys_values"] == []

    r = remoteci_context.post(
        "/api/v1/jobs/%s/kv" % job_id,
        data={"key": "mykey", "value": 123.123},
    )
    r.status_code == 201

    job = remoteci_context.get("/api/v1/jobs/%s" % job_id)
    assert job.data["job"]["keys_values"][0]["job_id"] == job_id
    assert job.data["job"]["keys_values"][0]["key"] == "mykey"
    assert job.data["job"]["keys_values"][0]["value"] == 123.123

    r = remoteci_context.delete(
        "/api/v1/jobs/%s/kv" % job_id,
        data={"key": "mykey"},
    )
    r.status_code == 204

    job = remoteci_context.get("/api/v1/jobs/%s" % job_id)
    job = job.data["job"]
    assert job["keys_values"] == []
