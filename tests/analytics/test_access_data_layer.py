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

from dci.analytics import access_data_layer as a_d_l

import datetime
import mock
import uuid


@mock.patch("dci.api.v1.jobs.get_utc_now")
def test_get_jobs(
    m_get_utc_now,
    session,
    hmac_client_team1,
    rhel_80_topic_id,
    rhel_80_component_id,
    team1_id,
):
    m_get_utc_now.return_value = datetime.datetime.utcnow() - datetime.timedelta(
        hours=2
    )

    pipeline = hmac_client_team1.post(
        "/api/v1/pipelines",
        data={"name": "pipeline1", "team_id": team1_id},
    )
    assert pipeline.status_code == 201
    pipeline_id = pipeline.data["pipeline"]["id"]

    jobs_ids = []
    data = {
        "components": [rhel_80_component_id],
        "topic_id": rhel_80_topic_id,
        "pipeline_id": pipeline_id,
    }
    for _ in range(4):
        j_id = hmac_client_team1.post("/api/v1/jobs", data=data).data["job"]["id"]
        jobs_ids.append(j_id)

    for j_id in jobs_ids[:2]:
        hmac_client_team1.post(
            "/api/v1/jobstates",
            data={"job_id": j_id, "comment": "kikoolol", "status": "running"},
        )

    jobs = a_d_l.get_jobs(session, 0, 10, "hours", 3)
    assert len(jobs) == 4
    job1 = [j for j in jobs if len(j["jobstates"]) > 0][0]
    assert "jobstates" in job1
    assert "files" in job1["jobstates"][0]
    assert "components" in job1
    assert "files" in job1
    assert "pipeline" in job1
    assert pipeline_id == job1["pipeline"]["id"]
    assert "product" in job1

    jobs = a_d_l.get_jobs(session, 0, 10, "hours", 1)
    assert len(jobs) == 2


@mock.patch("dci.api.v1.utils.get_utc_now")
def test_get_components(m_get_utc_now, session, client_admin, rhel_80_topic_id):
    m_get_utc_now.return_value = datetime.datetime.utcnow() - datetime.timedelta(
        hours=2
    )
    for i in range(5):
        client_admin.post(
            "/api/v1/components",
            data={
                "name": "pname%s" % uuid.uuid4(),
                "type": "gerrit_review",
                "topic_id": rhel_80_topic_id,
            },
        )

    components = a_d_l.get_components(session, 0, 10, "hours", 3)
    assert len(components) == 5
    assert "jobs" in components[0]

    components = a_d_l.get_components(session, 0, 10, "hours", 1)
    assert len(components) == 0
