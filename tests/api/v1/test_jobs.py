# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016, 2023 Red Hat, Inc
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
import pytest
import uuid

import datetime
from dci import dci_config
from dci.common import exceptions as dci_exc
from dci.common import utils
from dci.db import models2
from dci.stores import files_utils
from dci.stores.s3 import S3
from tests.data import JUNIT
import tests.utils as t_utils


AWSS3 = "dci.stores.s3.S3"


def test_create_jobs(
    remoteci_context, components_user_ids, job_user_id, team_user_id, topic_user_id
):
    data = {
        "comment": "kikoolol",
        "components": components_user_ids,
        "previous_job_id": job_user_id,
        "topic_id": topic_user_id,
        "data": {"config": "config"},
        "name": "my-job-name",
        "configuration": "my-configuration",
        "url": "http://example.com",
    }
    job = remoteci_context.post("/api/v1/jobs", data=data)
    job_id = job.data["job"]["id"]

    assert job.status_code == 201
    assert job.data["job"]["comment"] == "kikoolol"

    job = remoteci_context.get("/api/v1/jobs/%s" % job_id).data["job"]
    assert job["comment"] == "kikoolol"
    assert job["previous_job_id"] == job_user_id
    assert job["team_id"] == team_user_id
    assert job["data"] == {"config": "config"}
    assert job["name"] == "my-job-name"
    assert job["configuration"] == "my-configuration"
    assert job["url"] == "http://example.com"


def test_create_jobs_with_team_components(
    user,
    remoteci_context,
    components_user_ids,
    job_user_id,
    team_user_id,
    topic_user_id,
):
    data = {
        "name": "pname",
        "type": "mytest",
        "topic_id": topic_user_id,
        "team_id": team_user_id,
        "tags": ["tag1", "common"],
    }
    team_component = user.post("/api/v1/components", data=data).data["component"]

    components_user_ids.append(team_component["id"])
    data = {
        "comment": "kikoolol",
        "components": components_user_ids,
        "topic_id": topic_user_id,
    }
    job = remoteci_context.post("/api/v1/jobs", data=data)
    job_id = job.data["job"]["id"]

    assert job.status_code == 201
    assert job.data["job"]["comment"] == "kikoolol"

    job = remoteci_context.get("/api/v1/jobs/%s" % job_id)
    assert job.status_code == 200
    assert job.data["job"]["team_id"] == team_user_id

    job_components = remoteci_context.get("/api/v1/jobs/%s/components" % job_id).data
    job_components_ids = [cmpt["id"] for cmpt in job_components["components"]]
    assert set(job_components_ids) == set(components_user_ids)

    # get job with components embedded
    job = remoteci_context.get("/api/v1/jobs/%s?embed=components" % job_id).data
    job_components_ids = [cmpt["id"] for cmpt in job["job"]["components"]]
    assert set(job_components_ids) == set(components_user_ids)


def test_add_component_to_job(user, team_user_id, topic_user_id, job_user_id):
    data = {
        "name": "pname",
        "type": "gerrit_review",
        "url": "http://example.com/",
        "team_id": team_user_id,
        "topic_id": topic_user_id,
        "state": "active",
    }
    pc = user.post("/api/v1/components", data=data).data
    pc_id = pc["component"]["id"]
    p1 = user.post("/api/v1/jobs/%s/components" % job_user_id, data={"id": pc_id})
    assert p1.status_code == 201
    cmpts = user.get("/api/v1/jobs/%s/components" % job_user_id).data["components"]
    cmpt_found = False
    for c in cmpts:
        if c["id"] == pc_id:
            cmpt_found = True
    assert cmpt_found
    p1 = user.delete("/api/v1/jobs/%s/components/%s" % (job_user_id, pc_id))
    assert p1.status_code == 201
    cmpts = user.get("/api/v1/jobs/%s/components" % job_user_id).data["components"]
    cmpt_found = False
    for c in cmpts:
        if c["id"] == pc_id:
            cmpt_found = True
    assert not cmpt_found


def test_attach_component_from_other_team_to_job(
    admin, user, user2, team_user_id, team_user_id2, topic_user_id, job_user_id
):
    # create component as user2 under the team team_user_id2
    data = {
        "name": "pname",
        "type": "gerrit_review",
        "url": "http://example.com/",
        "team_id": team_user_id2,
        "topic_id": topic_user_id,
        "state": "active",
    }
    pc = user2.post("/api/v1/components", data=data).data
    pc_id = pc["component"]["id"]

    # attach this component to the job that belongs to the team team_user_id
    p1 = user.post("/api/v1/jobs/%s/components" % job_user_id, data={"id": pc_id})
    assert p1.status_code == 401

    # team_user_id as now access to team_user_id2's components
    pc = admin.post(
        "/api/v1/teams/%s/permissions/components" % team_user_id,
        data={"teams_ids": [team_user_id2]},
    )
    assert pc.status_code == 201

    p1 = user.post("/api/v1/jobs/%s/components" % job_user_id, data={"id": pc_id})
    assert p1.status_code == 201

    cmpts = user.get("/api/v1/jobs/%s/components" % job_user_id).data["components"]
    cmpt_found = False
    for c in cmpts:
        if c["id"] == pc_id:
            cmpt_found = True
    assert cmpt_found

    r = user.delete("/api/v1/jobs/%s/components/%s" % (job_user_id, pc_id))
    assert r.status_code == 201
    cmpts = user.get("/api/v1/jobs/%s/components" % job_user_id).data["components"]
    cmpt_found = False
    for c in cmpts:
        if c["id"] == pc_id:
            cmpt_found = True
    assert not cmpt_found


def test_add_component_with_no_team_to_job(
    user, admin, team_user_id, topic_user_id, job_user_id
):
    data = {
        "name": "pname",
        "type": "gerrit_review",
        "url": "http://example.com/",
        "topic_id": topic_user_id,
        "state": "active",
    }
    pc = admin.post("/api/v1/components", data=data).data
    pc_id = pc["component"]["id"]
    p1 = user.post("/api/v1/jobs/%s/components" % job_user_id, data={"id": pc_id})
    assert p1.status_code == 201
    cmpts = user.get("/api/v1/jobs/%s/components" % job_user_id).data["components"]
    cmpt_found = False
    for c in cmpts:
        if c["id"] == pc_id:
            cmpt_found = True
    assert cmpt_found


def test_create_jobs_bad_previous_job_id(
    remoteci_context, components_user_ids, topic_user_id
):
    data = {
        "comment": "kikoolol",
        "components": components_user_ids,
        "previous_job_id": "foo",
        "topic_id": topic_user_id,
    }
    r = remoteci_context.post("/api/v1/jobs", data=data)
    assert r.status_code == 400


def test_create_jobs_empty_comment(
    remoteci_context, components_user_ids, topic_user_id
):
    data = {"components": components_user_ids, "topic_id": topic_user_id}
    job = remoteci_context.post("/api/v1/jobs", data=data).data
    assert job["job"]["comment"] == ""

    job = remoteci_context.get("/api/v1/jobs/%s" % job["job"]["id"]).data
    assert job["job"]["comment"] == ""


def test_get_all_jobs(
    user, remoteci_context, topic_user_id, components_user_ids, team_user_id
):
    data = {"components_ids": components_user_ids, "topic_id": topic_user_id}
    job_1 = remoteci_context.post("/api/v1/jobs/schedule", data=data)
    job_1_id = job_1.data["job"]["id"]

    job_2 = remoteci_context.post("/api/v1/jobs/schedule", data=data)
    job_2_id = job_2.data["job"]["id"]

    db_all_jobs = user.get("/api/v1/jobs?sort=created_at").data
    db_all_jobs = db_all_jobs["jobs"]
    db_all_jobs_ids = [db_job["id"] for db_job in db_all_jobs]

    for j in db_all_jobs:
        assert "data" not in j

    assert db_all_jobs_ids == [job_1_id, job_2_id]


def test_get_jobs_with_query(
    user, remoteci_context, topic_user_id, components_user_ids, team_user_id, product
):
    data = {"components_ids": components_user_ids, "topic_id": topic_user_id}
    job_1 = remoteci_context.post("/api/v1/jobs/schedule", data=data).data["job"]
    status_reason = {"status_reason": "Invalid tasks"}
    remoteci_context.put(
        "/api/v1/jobs/%s" % job_1["id"],
        data=status_reason,
        headers={"If-match": job_1["etag"]},
    )

    job_2 = remoteci_context.post("/api/v1/jobs/schedule", data=data).data["job"]
    status_reason = {"status_reason": "Invalid tasks2"}
    remoteci_context.put(
        "/api/v1/jobs/%s" % job_2["id"],
        data=status_reason,
        headers={"If-match": job_2["etag"]},
    )

    jobs = user.get(
        "/api/v1/jobs?query=and(eq(product_id,%s),eq(status_reason,Invalid tasks))"
        % product["id"]
    ).data["jobs"]
    assert len(jobs) == 1

    jobs = user.get(
        "/api/v1/jobs?query=and(eq(product_id,%s),eq(status_reason,Invalid tasks2))"
        % product["id"]
    ).data["jobs"]
    assert len(jobs) == 1

    jobs = user.get(
        "/api/v1/jobs?query=and(eq(product_id,"
        + product["id"]
        + "),ilike(status_reason,Invalid tasks%))"
    ).data["jobs"]
    assert len(jobs) == 2

    jobs = user.get(
        "/api/v1/jobs?query=and(eq(product_id,%s),eq(status_reason,Invalid tasks3))"
        % product["id"]
    ).data["jobs"]
    assert len(jobs) == 0


def test_get_all_jobs_with_pagination(
    remoteci_context, components_user_ids, topic_user_id
):
    data = {"components": components_user_ids, "topic_id": topic_user_id}
    remoteci_context.post("/api/v1/jobs", data=data)
    remoteci_context.post("/api/v1/jobs", data=data)
    remoteci_context.post("/api/v1/jobs", data=data)
    remoteci_context.post("/api/v1/jobs", data=data)

    jobs = remoteci_context.get("/api/v1/jobs").data
    assert jobs["_meta"]["count"] == 4

    # verify limit and offset are working well
    jobs = remoteci_context.get("/api/v1/jobs?limit=2&offset=0").data
    assert len(jobs["jobs"]) == 2

    jobs = remoteci_context.get("/api/v1/jobs?limit=2&offset=2").data
    assert len(jobs["jobs"]) == 2

    # if offset is out of bound, the api returns an empty list
    jobs = remoteci_context.get("/api/v1/jobs?limit=5&offset=300")
    assert jobs.status_code == 200
    assert jobs.data["jobs"] == []


@mock.patch("dci.api.v1.notifications.job_dispatcher")
def test_get_all_jobs_with_subresources(
    job_dispatcher_mock,
    admin,
    remoteci_context,
    team_user_id,
    remoteci_user_id,
    components_user_ids,
    topic_user_id,
):
    # create 2 jobs and check meta data count
    data = {"components": components_user_ids, "topic_id": topic_user_id}
    remoteci_context.post("/api/v1/jobs", data=data)
    remoteci_context.post("/api/v1/jobs", data=data)

    jobs = admin.get("/api/v1/jobs").data

    for job in jobs["jobs"]:
        assert "team" in job
        assert job["team"]["id"] == team_user_id
        assert job["team_id"] == job["team"]["id"]
        assert "remoteci" in job
        assert job["remoteci"]["id"] == remoteci_user_id
        assert job["remoteci_id"] == job["remoteci"]["id"]
        assert "team" in job
        assert "results" in job
        assert "components" in job
        cur_set = set(i["id"] for i in job["components"])
        assert cur_set == set(components_user_ids)

    assert jobs["_meta"]["count"] == 2
    assert len(jobs["jobs"]) == 2
    jobs = admin.get("/api/v1/jobs").data
    for job in jobs["jobs"]:
        headers = {
            "DCI-JOB-ID": job["id"],
            "DCI-NAME": "name1.xml",
            "DCI-MIME": "application/junit",
            "Content-Type": "application/junit",
        }
        admin.post("/api/v1/files", headers=headers, data=JUNIT)
    jobs = admin.get("/api/v1/jobs").data
    assert jobs["_meta"]["count"] == 2
    assert len(jobs["jobs"]) == 2
    for job in jobs["jobs"]:
        assert len(job["results"]) == 1
        for result in job["results"]:
            assert "tests_cases" not in result


def test_get_all_jobs_with_duplicated_embed(
    remoteci_context, rhel_80_component, rhel_80_topic
):
    data = {"topic_id": rhel_80_topic["id"], "components": [rhel_80_component["id"]]}
    remoteci_context.post("/api/v1/jobs", data=data)
    query_embed = "/api/v1/jobs?embed=" "topic,components," "files,topic,team,remoteci"
    jobs = remoteci_context.get(query_embed).data
    assert len(jobs["jobs"]) == 1
    assert len(jobs["jobs"][0]["components"]) == 1
    assert "topic" in jobs["jobs"][0]
    assert "remoteci" in jobs["jobs"][0]


def test_get_all_jobs_with_embed_and_limit(
    remoteci_context, rhel_80_topic, rhel_80_component
):
    # create 2 jobs and check meta data count
    data = {"topic_id": rhel_80_topic["id"], "components": [rhel_80_component["id"]]}
    remoteci_context.post("/api/v1/jobs", data=data)
    remoteci_context.post("/api/v1/jobs", data=data)

    # verify embed with all embedded options
    query_embed = "/api/v1/jobs?embed=components&limit=1&offset=0"
    jobs = remoteci_context.get(query_embed).data

    assert len(jobs["jobs"]) == 1
    assert len(jobs["jobs"][0]["components"]) == 1


def test_update_job(admin, job_user_id):
    data_update = {
        "status": "failure",
        "comment": "bar",
        "status_reason": "lol",
        "url": "http://example2.com",
    }

    res = admin.get("/api/v1/jobs/%s" % job_user_id)
    job = res.data["job"]

    res = admin.put(
        "/api/v1/jobs/%s" % job_user_id,
        data=data_update,
        headers={"If-match": job["etag"]},
    )
    assert res.status_code == 200
    job = res.data["job"]

    assert res.status_code == 200
    assert job["status"] == "failure"
    assert job["comment"] == "bar"
    assert job["status_reason"] == "lol"
    assert job["url"] == "http://example2.com"


def test_success_update_job_status(admin, job_user_id):
    job = admin.get("/api/v1/jobs/%s" % job_user_id)
    job = job.data["job"]

    assert job["status"] == "new"

    data_update = {"status": "pre-run"}
    job = admin.put(
        "/api/v1/jobs/%s" % job_user_id,
        data=data_update,
        headers={"If-match": job["etag"]},
    )
    job = admin.get("/api/v1/jobs/%s" % job_user_id).data["job"]

    assert job["status"] == "pre-run"

    data_update = {"status": "failure"}
    job = admin.put(
        "/api/v1/jobs/%s" % job_user_id,
        data=data_update,
        headers={"If-match": job["etag"]},
    )
    job = admin.get("/api/v1/jobs/%s" % job_user_id).data["job"]

    assert job["status"] == "failure"


def test_job_duration(session, admin, job_user_id):
    job = admin.get("/api/v1/jobs/%s" % job_user_id)
    job = job.data["job"]
    assert job["status"] == "new"
    # update the job with a created_at 5 seconds in the past
    job = session.query(models2.Job).filter(models2.Job.id == job_user_id).one()
    job.created_at = datetime.datetime.utcnow() - datetime.timedelta(0, 5)
    session.commit()

    data = {"job_id": job_user_id, "status": "running"}
    js = admin.post("/api/v1/jobstates", data=data)
    assert js.status_code == 201
    job = admin.get("/api/v1/jobs/%s" % job_user_id)
    # check those 5 seconds
    assert job.data["job"]["duration"] >= 5


def test_first_job_duration(admin, job_user_id, topic, remoteci_context):
    job = admin.get("/api/v1/jobs/%s" % job_user_id).data["job"]
    assert job["duration"] == 0

    job = remoteci_context.post(
        "/api/v1/jobs/schedule", data={"topic_id": topic["id"]}
    ).data["job"]
    assert job["duration"] == 0
    job = admin.get("/api/v1/jobs/%s" % job["id"]).data["job"]
    assert job["duration"] == 0


def test_get_all_jobs_with_where(admin, team_user_id, job_user_id):
    db_job = admin.get("/api/v1/jobs?where=id:%s" % job_user_id).data
    db_job_id = db_job["jobs"][0]["id"]
    assert db_job_id == job_user_id

    db_job = admin.get("/api/v1/jobs?where=team_id:%s" % team_user_id).data
    db_job_id = db_job["jobs"][0]["id"]
    assert db_job_id == job_user_id

    db_job = admin.get(
        "/api/v1/jobs?where=id:%s,team_id:%s" % (job_user_id, team_user_id)
    ).data
    db_job_id = db_job["jobs"][0]["id"]
    assert db_job_id == job_user_id


def test_get_all_jobs_with_pipeline(
    remoteci_context, user, team_user_id, topic_user_id
):
    pipeline = user.post(
        "/api/v1/pipelines",
        data={"name": "pipeline1", "team_id": team_user_id},
    )
    pipeline_id = pipeline.data["pipeline"]["id"]
    remoteci_context.post(
        "/api/v1/jobs/schedule",
        data={"pipeline_id": pipeline_id, "topic_id": topic_user_id},
    )
    remoteci_context.post(
        "/api/v1/jobs/schedule",
        data={"pipeline_id": pipeline_id, "topic_id": topic_user_id},
    )

    jobs = user.get("/api/v1/jobs").data["jobs"]
    for j in jobs:
        assert "pipeline" in j
        assert j["pipeline"]["name"] == "pipeline1"


def test_where_invalid(admin):
    err = admin.get("/api/v1/jobs?where=id")

    assert err.status_code == 400
    assert err.data["message"] == "Request malformed"
    assert err.data["payload"]["error"] == "where: 'id' is not a 'key value csv'"


def test_get_all_jobs_with_sort(remoteci_context, components_user_ids, topic_user_id):
    # create 3 jobs ordered by created time
    data = {"components": components_user_ids, "topic_id": topic_user_id}
    job_1 = remoteci_context.post("/api/v1/jobs", data=data).data["job"]
    job_1.pop("data")
    job_2 = remoteci_context.post("/api/v1/jobs", data=data).data["job"]
    job_2.pop("data")
    job_3 = remoteci_context.post("/api/v1/jobs", data=data).data["job"]
    job_3.pop("data")

    jobs = remoteci_context.get("/api/v1/jobs?sort=created_at").data
    assert jobs["jobs"][0]["id"] == job_1["id"]
    assert jobs["jobs"][1]["id"] == job_2["id"]
    assert jobs["jobs"][2]["id"] == job_3["id"]

    # reverse order by created_at
    jobs = remoteci_context.get("/api/v1/jobs?sort=-created_at").data
    assert jobs["jobs"][0]["id"] == job_3["id"]
    assert jobs["jobs"][1]["id"] == job_2["id"]
    assert jobs["jobs"][2]["id"] == job_1["id"]


def test_get_jobs_by_product(user, product):
    jobs = user.get("/api/v1/jobs?where=product_id:%s" % product["id"]).data["jobs"]
    for job in jobs:
        assert job["product_id"] == product["id"]


def test_get_job_by_id(
    remoteci_context, components_user_ids, team_user_id, topic_user_id
):
    job = remoteci_context.post(
        "/api/v1/jobs",
        data={"components": components_user_ids, "topic_id": topic_user_id},
    )
    job_id = job.data["job"]["id"]

    job = remoteci_context.get("/api/v1/jobs/%s" % job_id)
    assert job.status_code == 200

    job = job.data
    assert job["job"]["id"] == job_id
    assert "results" in job["job"]
    assert "remoteci" in job["job"]
    assert "components" in job["job"]
    assert "topic" in job["job"]
    assert "team" in job["job"]
    assert "jobstates" in job["job"]
    assert "files" in job["job"]


def test_get_jobstates_by_job_id(admin, user, job_user_id):
    data = {"status": "new", "job_id": job_user_id}
    jobstate_ids = set(
        [
            admin.post("/api/v1/jobstates", data=data).data["jobstate"]["id"],
            admin.post("/api/v1/jobstates", data=data).data["jobstate"]["id"],
        ]
    )

    jobstates = user.get("/api/v1/jobs/%s/jobstates" % job_user_id)
    assert jobstates.status_code == 200
    jobstates = jobstates.data["jobstates"]

    found_jobstate_ids = set(i["id"] for i in jobstates)
    assert jobstate_ids == found_jobstate_ids

    # verify embed with all embedded options
    jobstates = admin.get("/api/v1/jobs/%s?embed=jobstates" % job_user_id)
    assert len(jobstates.data["job"]["jobstates"]) == len(found_jobstate_ids)


def test_get_jobstates_by_job_id_sorted(admin, user, job_user_id, session):
    data = {"status": "new", "job_id": job_user_id}
    jobstate_ids = [
        admin.post("/api/v1/jobstates", data=data).data["jobstate"]["id"],
        admin.post("/api/v1/jobstates", data=data).data["jobstate"]["id"],
        admin.post("/api/v1/jobstates", data=data).data["jobstate"]["id"],
    ]

    job = user.get("/api/v1/jobs/%s" % job_user_id)
    assert job.status_code == 200

    for i in range(3):
        assert jobstate_ids[i] == job.data["job"]["jobstates"][i]["id"]

    jobstate = (
        session.query(models2.Jobstate)
        .filter(models2.Jobstate.id == jobstate_ids[2])
        .one()
    )
    jobstate.created_at = datetime.datetime.utcnow() - datetime.timedelta(days=1)
    session.commit()

    job = user.get("/api/v1/jobs/%s" % job_user_id)
    assert job.status_code == 200
    assert jobstate_ids[2] == job.data["job"]["jobstates"][0]["id"]
    assert jobstate_ids[0] == job.data["job"]["jobstates"][1]["id"]
    assert jobstate_ids[1] == job.data["job"]["jobstates"][2]["id"]


def test_get_jobstates_by_job_id_by_epm(epm, admin, job_user_id):
    data = {"status": "new", "job_id": job_user_id}
    jobstate_ids = set(
        [
            admin.post("/api/v1/jobstates", data=data).data["jobstate"]["id"],
            admin.post("/api/v1/jobstates", data=data).data["jobstate"]["id"],
        ]
    )

    jobstates = epm.get("/api/v1/jobs/%s/jobstates" % job_user_id)
    assert jobstates.status_code == 200
    jobstates = jobstates.data["jobstates"]

    found_jobstate_ids = set(i["id"] for i in jobstates)
    assert jobstate_ids == found_jobstate_ids

    # verify embed with all embedded options
    jobstates = admin.get("/api/v1/jobs/%s?embed=jobstates" % job_user_id)
    assert len(jobstates.data["job"]["jobstates"]) == len(found_jobstate_ids)


def test_get_jobstates_by_job_id_with_embed(admin, job_user_id, jobstate_user_id):
    with mock.patch(AWSS3, spec=S3) as mock_s3:
        mockito = mock.MagicMock()

        head_result = {
            "etag": utils.gen_etag(),
            "content-type": "stream",
            "content-length": 7,
        }

        mockito.head.return_value = head_result
        mock_s3.return_value = mockito
        headers = {"DCI-JOBSTATE-ID": jobstate_user_id, "DCI-NAME": "name1"}
        pfile = admin.post("/api/v1/files", headers=headers, data="kikoolol").data
        file1_id = pfile["file"]["id"]
        headers = {"DCI-JOBSTATE-ID": jobstate_user_id, "DCI-NAME": "name2"}
        pfile = admin.post("/api/v1/files", headers=headers, data="kikoolol").data
        file2_id = pfile["file"]["id"]
        jobstates = admin.get("/api/v1/jobs/%s/jobstates" "?embed=files" % job_user_id)
        jobstate = jobstates.data["jobstates"][0]
        assert set((jobstate["files"][0]["id"], jobstate["files"][1]["id"])) == set(
            (file1_id, file2_id)
        )


def test_get_job_not_found(admin):
    result = admin.get("/api/v1/jobs/%s" % uuid.uuid4())
    assert result.status_code == 404


def test_get_jobs_with_schedule(remoteci_context, topic_user_id, components_user_ids):
    # schedule a job
    data = {"topic_id": topic_user_id, "comment": "kikoolol"}
    job = remoteci_context.post("/api/v1/jobs/schedule", data=data)
    assert job.status_code == 201
    job_id = job.data["job"]["id"]
    assert job.data["job"]["comment"] == "kikoolol"

    # get the components of the scheduled jobs
    job_components = remoteci_context.get("/api/v1/jobs/%s/components" % job_id).data
    for c in job_components["components"]:
        url = "/api/v1/components/%s?embed=jobs" % c["id"]
        component = remoteci_context.get(url).data
        assert component["component"]["jobs"][0]["id"] == job_id


def test_delete_job_by_id(remoteci_context, components_user_ids, topic_user_id):
    job = remoteci_context.post(
        "/api/v1/jobs",
        data={"components": components_user_ids, "topic_id": topic_user_id},
    )
    job_id = job.data["job"]["id"]
    job_etag = job.headers.get("ETag")
    assert job.status_code == 201

    job = remoteci_context.get("/api/v1/jobs/%s" % job_id)
    assert job.status_code == 200

    deleted_job = remoteci_context.delete(
        "/api/v1/jobs/%s" % job_id, headers={"If-match": job_etag}
    )
    assert deleted_job.status_code == 204

    job = remoteci_context.get("/api/v1/jobs/%s" % job_id)
    assert job.status_code == 404


def test_delete_job_archive_dependencies(admin, job_user_id):
    with mock.patch(AWSS3, spec=S3) as mock_s3:
        mockito = mock.MagicMock()

        head_result = {
            "etag": utils.gen_etag(),
            "content-type": "stream",
            "content-length": 7,
        }

        mockito.head.return_value = head_result
        mock_s3.return_value = mockito

        headers = {
            "DCI-JOB-ID": job_user_id,
            "DCI-NAME": "afile.txt",
            "Content-Type": "text/plain",
        }

        file = admin.post("/api/v1/files", headers=headers, data="content")
        assert file.status_code == 201

        url = "/api/v1/jobs/%s" % job_user_id
        job = admin.get(url)
        etag = job.data["job"]["etag"]
        assert job.status_code == 200

        deleted_job = admin.delete(url, headers={"If-match": etag})
        assert deleted_job.status_code == 204

        url = "/api/v1/files/%s" % file.data["file"]["id"]
        file = admin.get(url)
        assert file.status_code == 404


# Tests for the isolation


def test_get_all_jobs_as_user(user, team_user_id, job_user_id):
    jobs = user.get("/api/v1/jobs")
    assert jobs.status_code == 200
    assert jobs.data["_meta"]["count"] == 1
    for job in jobs.data["jobs"]:
        assert job["team_id"] == team_user_id


def test_get_all_jobs_as_epm(epm, team_user_id, job_user_id):
    jobs = epm.get("/api/v1/jobs")
    assert jobs.status_code == 200
    assert jobs.data["_meta"]["count"] == 1
    for job in jobs.data["jobs"]:
        assert job["team_id"] == team_user_id


def test_get_job_as_user(user, remoteci_context, components_user_ids, topic_user_id):
    job = remoteci_context.post(
        "/api/v1/jobs",
        data={"components": components_user_ids, "topic_id": topic_user_id},
    ).data
    job_id = job["job"]["id"]
    job = user.get("/api/v1/jobs/%s" % job_id)
    assert job.status_code == 200


def test_delete_job_as_user(user, job_user_id):
    job = user.get("/api/v1/jobs/%s" % job_user_id)
    job_etag = job.headers.get("ETag")

    job_delete = user.delete(
        "/api/v1/jobs/%s" % job_user_id, headers={"If-match": job_etag}
    )

    assert job_delete.status_code == 204

    job = user.get("/api/v1/jobs/%s" % job_user_id)
    assert job.status_code == 404


def test_nrt_delete_job_as_user_and_red_hat(
    admin, team_redhat_id, user_id, user, job_user_id
):
    add_user_in_redhat_team = admin.post(
        "/api/v1/teams/%s/users/%s" % (team_redhat_id, user_id), data={}
    )
    assert add_user_in_redhat_team.status_code == 201

    job = user.get("/api/v1/jobs/%s" % job_user_id)
    job_etag = job.headers.get("ETag")
    job_delete = user.delete(
        "/api/v1/jobs/%s" % job_user_id, headers={"If-match": job_etag}
    )
    assert job_delete.status_code == 204
    job = user.get("/api/v1/jobs/%s" % job_user_id)
    assert job.status_code == 404


def test_when_a_user_delete_a_job_we_add_log_entry(session, user, user_id, job_user_id):
    job = user.get("/api/v1/jobs/%s" % job_user_id)
    job_etag = job.headers.get("ETag")

    job_delete = user.delete(
        "/api/v1/jobs/%s" % job_user_id, headers={"If-match": job_etag}
    )
    assert job_delete.status_code == 204

    logs = session.query(models2.Log).all()
    assert len(logs) == 1
    assert str(logs[0].user_id) == user_id
    assert logs[0].action == "delete_job_by_id"


def test_create_file_for_job_id(
    user, remoteci_context, components_user_ids, topic_user_id
):
    with mock.patch(AWSS3, spec=S3) as mock_s3:
        mockito = mock.MagicMock()
        head_result = {
            "etag": utils.gen_etag(),
            "content-type": "stream",
            "content-length": 7,
        }
        mockito.head.return_value = head_result
        mock_s3.return_value = mockito
        # create a job
        job = remoteci_context.post(
            "/api/v1/jobs",
            data={"components": components_user_ids, "topic_id": topic_user_id},
        )
        job_id = job.data["job"]["id"]
        assert job.status_code == 201

        # create a file
        headers = {"DCI-JOB-ID": job_id, "DCI-NAME": "foobar"}
        file = user.post("/api/v1/files", headers=headers)
        file_id = file.data["file"]["id"]
        file = user.get("/api/v1/files/%s" % file_id).data
        assert file["file"]["name"] == "foobar"


def test_get_files_by_job_id(user, job_user_id, file_job_user_id):
    # get files from job
    file_from_job = user.get("/api/v1/jobs/%s/files" % job_user_id)
    assert file_from_job.status_code == 200
    assert file_from_job.data["_meta"]["count"] == 1


def test_get_files_by_job_id_as_epm(epm, job_user_id, file_job_user_id):
    # get files from job
    file_from_job = epm.get("/api/v1/jobs/%s/files" % job_user_id)
    assert file_from_job.status_code == 200
    assert file_from_job.data["_meta"]["count"] == 1


@mock.patch("dci.api.v1.notifications.job_dispatcher")
def test_get_results_by_job_id(job_dispatcher_mock, user, job_user_id):
    headers = {
        "DCI-JOB-ID": job_user_id,
        "Content-Type": "application/junit",
        "DCI-MIME": "application/junit",
        "DCI-NAME": "res_junit.xml",
    }

    user.post("/api/v1/files", headers=headers, data=JUNIT)

    # get file from job
    file_from_job = user.get("/api/v1/jobs/%s/results" % job_user_id)
    assert file_from_job.status_code == 200
    assert file_from_job.data["_meta"]["count"] == 1
    assert file_from_job.data["results"][0]["total"] == 6


def test_purge(user, admin, job_user_id, team_user_id):
    file_id1 = t_utils.create_file(user, job_user_id, "kikoolol", "content")["id"]
    job = user.get("/api/v1/jobs/%s" % job_user_id).data["job"]

    djob = admin.delete(
        "/api/v1/jobs/%s" % job_user_id, headers={"If-match": job["etag"]}
    )
    assert djob.status_code == 204
    to_purge_jobs = admin.get("/api/v1/jobs/purge").data
    assert len(to_purge_jobs["jobs"]) == 1
    to_purge_files = admin.get("/api/v1/files/purge").data
    assert len(to_purge_files["files"]) == 1

    admin.post("/api/v1/jobs/purge")
    path1 = files_utils.build_file_path(team_user_id, job_user_id, file_id1)
    store = dci_config.get_store()
    # the purge removed the file from the backend, get() must raise exception
    with pytest.raises(dci_exc.StoreException):
        store.get("files", path1)

    admin.post("/api/v1/jobs/purge")
    to_purge_jobs = admin.get("/api/v1/jobs/purge").data
    assert len(to_purge_jobs["jobs"]) == 0
    to_purge_files = admin.get("/api/v1/files/purge").data
    assert len(to_purge_files["files"]) == 0


def test_purge_failure(user, admin, job_user_id, team_user_id):
    file_id1 = t_utils.create_file(user, job_user_id, "kikoolol", "content")["id"]
    job = user.get("/api/v1/jobs/%s" % job_user_id).data["job"]

    djob = admin.delete(
        "/api/v1/jobs/%s" % job_user_id, headers={"If-match": job["etag"]}
    )
    assert djob.status_code == 204
    to_purge_jobs = admin.get("/api/v1/jobs/purge").data
    assert len(to_purge_jobs["jobs"]) == 1
    to_purge_files = admin.get("/api/v1/files/purge").data
    assert len(to_purge_files["files"]) == 1

    # purge will fail
    with mock.patch("dci.stores.s3.S3.delete") as mock_delete:
        mock_delete.side_effect = dci_exc.StoreException("error")
        purge_res = admin.post("/api/v1/jobs/purge")
        assert purge_res.status_code == 400
        path1 = files_utils.build_file_path(team_user_id, job_user_id, file_id1)
        store = dci_config.get_store()
        # because the delete fail the backend didn't remove the files and the
        # files are still in the database
        store.get("files", path1)
    to_purge_files = admin.get("/api/v1/files/purge").data
    assert len(to_purge_files["files"]) == 1
    to_purge_jobs = admin.get("/api/v1/jobs/purge").data
    assert len(to_purge_jobs["jobs"]) == 1


def test_nrt_get_then_put_on_job_with_no_error(user, job_user_id):
    r = user.get("/api/v1/jobs/%s" % job_user_id)
    assert r.status_code == 200
    job = r.data["job"]
    r = user.put(
        "/api/v1/jobs/%s" % job_user_id,
        data=job,
        headers={"If-match": job["etag"]},
    )
    assert r.status_code == 200
