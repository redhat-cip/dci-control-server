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


def test_update_jobs(client_admin, hmac_client_team1, team1_job_id, rhel_80_topic):
    # test update schedule latest components
    data = {
        "name": "pname",
        "type": "compose",
        "url": "http://example.com/",
        "topic_id": rhel_80_topic["id"],
        "state": "active",
    }
    client_admin.post("/api/v1/components", data=data).data["component"]["id"]
    data.update({"name": "pname1"})
    latest_component_id = client_admin.post("/api/v1/components", data=data).data[
        "component"
    ]["id"]
    data.update({"name": "pname2"})

    r = hmac_client_team1.post("/api/v1/jobs/%s/update" % team1_job_id)
    assert r.status_code == 201
    update_job = r.data["job"]

    assert update_job["update_previous_job_id"] == team1_job_id
    assert update_job["topic_id"] == rhel_80_topic["id"]

    updated_cmpts = client_admin.get(
        "/api/v1/jobs/%s/components" % update_job["id"]
    ).data["components"]
    assert len(updated_cmpts) == 1
    assert updated_cmpts[0]["id"] == latest_component_id
