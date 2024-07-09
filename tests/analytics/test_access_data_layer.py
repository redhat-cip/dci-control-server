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
    remoteci_context,
    components_user_ids,
    topic_user_id,
    team_user_id,
):
    m_get_utc_now.return_value = datetime.datetime.utcnow() - datetime.timedelta(
        hours=2
    )

    pipeline = remoteci_context.post(
        "/api/v1/pipelines",
        data={"name": "pipeline1", "team_id": team_user_id},
    )
    assert pipeline.status_code == 201
    pipeline_id = pipeline.data["pipeline"]["id"]

    jobs_ids = []
    data = {
        "components": components_user_ids,
        "topic_id": topic_user_id,
        "pipeline_id": pipeline_id,
    }
    for _ in range(4):
        j_id = remoteci_context.post("/api/v1/jobs", data=data).data["job"]["id"]
        jobs_ids.append(j_id)

    for j_id in jobs_ids[:2]:
        remoteci_context.post(
            "/api/v1/jobstates",
            data={"job_id": j_id, "comment": "kikoolol", "status": "running"},
        )

    jobs = a_d_l.get_jobs(session, 0, 10, "hours", 3)
    assert len(jobs) == 4
    assert "jobstates" in jobs[0]
    assert "files" in jobs[0]["jobstates"][0]
    assert "components" in jobs[0]
    assert "files" in jobs[0]
    assert "pipeline" in jobs[0]
    assert pipeline_id == jobs[0]["pipeline"]["id"]
    assert "product" in jobs[0]

    jobs = a_d_l.get_jobs(session, 0, 10, "hours", 1)
    assert len(jobs) == 2


@mock.patch("dci.api.v1.components.v1_utils.datetime")
def test_get_components(m_datetime, session, admin, topic_id):
    m_utcnow = mock.MagicMock()
    m_datetime.datetime.utcnow.return_value = m_utcnow
    m_utcnow.isoformat.return_value = (
        datetime.datetime.utcnow() - datetime.timedelta(hours=2)
    ).isoformat()
    for i in range(5):
        admin.post(
            "/api/v1/components",
            data={
                "name": "pname%s" % uuid.uuid4(),
                "type": "gerrit_review",
                "topic_id": topic_id,
            },
        )

    components = a_d_l.get_components(session, 0, 10, "hours", 3)
    assert len(components) == 5
    assert "jobs" in components[0]

    components = a_d_l.get_components(session, 0, 10, "hours", 1)
    assert len(components) == 0
