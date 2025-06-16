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
    hmac_client_team1, team1_job_id, team1_id, rhel_80_topic_id, rhel_80_component_id
):
    data = {
        "comment": "kikoolol",
        "components": [rhel_80_component_id],
        "previous_job_id": team1_job_id,
        "topic_id": rhel_80_topic_id,
        "data": {"config": "config"},
        "name": "my-job-name",
        "configuration": "my-configuration",
        "url": "http://example.com",
    }
    job = hmac_client_team1.post("/api/v1/jobs", data=data)
    job_id = job.data["job"]["id"]

    assert job.status_code == 201
    assert job.data["job"]["comment"] == "kikoolol"

    job = hmac_client_team1.get("/api/v1/jobs/%s" % job_id).data["job"]
    assert job["comment"] == "kikoolol"
    assert job["previous_job_id"] == team1_job_id
    assert job["team_id"] == team1_id
    assert job["data"] == {"config": "config"}
    assert job["name"] == "my-job-name"
    assert job["configuration"] == "my-configuration"
    assert job["url"] == "http://example.com"


def test_create_jobs_with_team_components(
    client_user1,
    hmac_client_team1,
    team1_id,
    rhel_80_topic_id,
    rhel_80_component_id,
):
    data = {
        "name": "pname",
        "type": "mytest",
        "topic_id": rhel_80_topic_id,
        "team_id": team1_id,
        "tags": ["tag1", "common"],
    }
    team_component = client_user1.post("/api/v1/components", data=data).data[
        "component"
    ]
    components_ids = [rhel_80_component_id]
    components_ids.append(team_component["id"])
    data = {
        "comment": "kikoolol",
        "topic_id": rhel_80_topic_id,
        "components": components_ids,
    }
    job = hmac_client_team1.post("/api/v1/jobs", data=data)
    job_id = job.data["job"]["id"]

    assert job.status_code == 201
    assert job.data["job"]["comment"] == "kikoolol"

    job = hmac_client_team1.get("/api/v1/jobs/%s" % job_id)
    assert job.status_code == 200
    assert job.data["job"]["team_id"] == team1_id

    job_components = hmac_client_team1.get("/api/v1/jobs/%s/components" % job_id).data
    job_components_ids = [cmpt["id"] for cmpt in job_components["components"]]
    assert set(job_components_ids) == set(components_ids)

    # get job with components embedded
    job = hmac_client_team1.get("/api/v1/jobs/%s?embed=components" % job_id).data
    job_components_ids = [cmpt["id"] for cmpt in job["job"]["components"]]
    assert set(job_components_ids) == set(components_ids)


def test_add_component_to_job(client_user1, team1_id, rhel_80_topic_id, team1_job_id):
    data = {
        "name": "pname",
        "type": "gerrit_review",
        "url": "http://example.com/",
        "team_id": team1_id,
        "topic_id": rhel_80_topic_id,
        "state": "active",
    }
    pc = client_user1.post("/api/v1/components", data=data).data
    pc_id = pc["component"]["id"]
    p1 = client_user1.post(
        "/api/v1/jobs/%s/components" % team1_job_id, data={"id": pc_id}
    )
    assert p1.status_code == 201
    cmpts = client_user1.get("/api/v1/jobs/%s/components" % team1_job_id).data[
        "components"
    ]
    cmpt_found = False
    for c in cmpts:
        if c["id"] == pc_id:
            cmpt_found = True
    assert cmpt_found
    p1 = client_user1.delete("/api/v1/jobs/%s/components/%s" % (team1_job_id, pc_id))
    assert p1.status_code == 201
    cmpts = client_user1.get("/api/v1/jobs/%s/components" % team1_job_id).data[
        "components"
    ]
    cmpt_found = False
    for c in cmpts:
        if c["id"] == pc_id:
            cmpt_found = True
    assert not cmpt_found


def test_attach_component_from_other_team_to_job(
    client_admin,
    client_user1,
    client_user2,
    team1_id,
    team2_id,
    rhel_80_topic_id,
    team1_job_id,
):
    # create component as user2 under the team team_user_id2
    data = {
        "name": "pname",
        "type": "gerrit_review",
        "url": "http://example.com/",
        "team_id": team2_id,
        "topic_id": rhel_80_topic_id,
        "state": "active",
    }
    pc = client_user2.post("/api/v1/components", data=data).data
    pc_id = pc["component"]["id"]

    # attach this component to the job that belongs to the team team_user_id
    p1 = client_user1.post(
        "/api/v1/jobs/%s/components" % team1_job_id, data={"id": pc_id}
    )
    assert p1.status_code == 401

    # team_user_id as now access to team_user_id2's components
    pc = client_admin.post(
        "/api/v1/teams/%s/permissions/components" % team1_id,
        data={"teams_ids": [team2_id]},
    )
    assert pc.status_code == 201

    p1 = client_user1.post(
        "/api/v1/jobs/%s/components" % team1_job_id, data={"id": pc_id}
    )
    assert p1.status_code == 201

    cmpts = client_user1.get("/api/v1/jobs/%s/components" % team1_job_id).data[
        "components"
    ]
    cmpt_found = False
    for c in cmpts:
        if c["id"] == pc_id:
            cmpt_found = True
    assert cmpt_found

    r = client_user1.delete("/api/v1/jobs/%s/components/%s" % (team1_job_id, pc_id))
    assert r.status_code == 201
    cmpts = client_user1.get("/api/v1/jobs/%s/components" % team1_job_id).data[
        "components"
    ]
    cmpt_found = False
    for c in cmpts:
        if c["id"] == pc_id:
            cmpt_found = True
    assert not cmpt_found


def test_add_component_with_no_team_to_job(
    client_user1, client_admin, team1_id, rhel_80_topic_id, team1_job_id
):
    data = {
        "name": "pname",
        "type": "gerrit_review",
        "url": "http://example.com/",
        "topic_id": rhel_80_topic_id,
        "state": "active",
    }
    pc = client_admin.post("/api/v1/components", data=data).data
    pc_id = pc["component"]["id"]
    p1 = client_user1.post(
        "/api/v1/jobs/%s/components" % team1_job_id, data={"id": pc_id}
    )
    assert p1.status_code == 201
    cmpts = client_user1.get("/api/v1/jobs/%s/components" % team1_job_id).data[
        "components"
    ]
    cmpt_found = False
    for c in cmpts:
        if c["id"] == pc_id:
            cmpt_found = True
    assert cmpt_found


def test_create_jobs_bad_previous_job_id(
    hmac_client_team1, rhel_80_topic_id, rhel_80_component_id
):
    data = {
        "comment": "kikoolol",
        "components": [rhel_80_component_id],
        "previous_job_id": "foo",
        "topic_id": rhel_80_topic_id,
    }
    r = hmac_client_team1.post("/api/v1/jobs", data=data)
    assert r.status_code == 400


def test_create_jobs_empty_comment(
    hmac_client_team1, rhel_80_topic_id, rhel_80_component_id
):
    data = {"components": [rhel_80_component_id], "topic_id": rhel_80_topic_id}
    job = hmac_client_team1.post("/api/v1/jobs", data=data).data
    assert job["job"]["comment"] == ""

    job = hmac_client_team1.get("/api/v1/jobs/%s" % job["job"]["id"]).data
    assert job["job"]["comment"] == ""


def test_get_all_jobs(
    client_user1, hmac_client_team1, rhel_80_topic_id, rhel_80_component_id
):
    data = {"components_ids": [rhel_80_component_id], "topic_id": rhel_80_topic_id}
    job_1 = hmac_client_team1.post("/api/v1/jobs/schedule", data=data)
    job_1_id = job_1.data["job"]["id"]

    job_2 = hmac_client_team1.post("/api/v1/jobs/schedule", data=data)
    job_2_id = job_2.data["job"]["id"]

    db_all_jobs = client_user1.get("/api/v1/jobs?sort=created_at").data
    db_all_jobs = db_all_jobs["jobs"]
    db_all_jobs_ids = [db_job["id"] for db_job in db_all_jobs]

    for j in db_all_jobs:
        assert "data" not in j

    assert db_all_jobs_ids == [job_1_id, job_2_id]


def test_get_jobs_with_query(
    client_user1,
    hmac_client_team1,
    rhel_80_topic_id,
    rhel_80_component_id,
    rhel_product,
):
    data = {"components_ids": [rhel_80_component_id], "topic_id": rhel_80_topic_id}
    job_1 = hmac_client_team1.post("/api/v1/jobs/schedule", data=data).data["job"]
    status_reason = {"status_reason": "Invalid tasks"}
    hmac_client_team1.put(
        "/api/v1/jobs/%s" % job_1["id"],
        data=status_reason,
        headers={"If-match": job_1["etag"]},
    )

    job_2 = hmac_client_team1.post("/api/v1/jobs/schedule", data=data).data["job"]
    status_reason = {"status_reason": "Invalid tasks2"}
    hmac_client_team1.put(
        "/api/v1/jobs/%s" % job_2["id"],
        data=status_reason,
        headers={"If-match": job_2["etag"]},
    )

    jobs = client_user1.get(
        "/api/v1/jobs?query=and(eq(product_id,%s),eq(status_reason,Invalid tasks))"
        % rhel_product["id"]
    ).data["jobs"]
    assert len(jobs) == 1

    jobs = client_user1.get(
        "/api/v1/jobs?query=and(eq(product_id,%s),eq(status_reason,Invalid tasks2))"
        % rhel_product["id"]
    ).data["jobs"]
    assert len(jobs) == 1

    jobs = client_user1.get(
        "/api/v1/jobs?query=and(eq(product_id,"
        + rhel_product["id"]
        + "),ilike(status_reason,Invalid tasks%))"
    ).data["jobs"]
    assert len(jobs) == 2

    jobs = client_user1.get(
        "/api/v1/jobs?query=and(eq(product_id,%s),eq(status_reason,Invalid tasks3))"
        % rhel_product["id"]
    ).data["jobs"]
    assert len(jobs) == 0


def test_get_all_jobs_with_pagination(
    hmac_client_team1, rhel_80_topic_id, rhel_80_component_id
):
    data = {"components": [rhel_80_component_id], "topic_id": rhel_80_topic_id}
    hmac_client_team1.post("/api/v1/jobs", data=data)
    hmac_client_team1.post("/api/v1/jobs", data=data)
    hmac_client_team1.post("/api/v1/jobs", data=data)
    hmac_client_team1.post("/api/v1/jobs", data=data)

    jobs = hmac_client_team1.get("/api/v1/jobs").data
    assert jobs["_meta"]["count"] == 4

    # verify limit and offset are working well
    jobs = hmac_client_team1.get("/api/v1/jobs?limit=2&offset=0").data
    assert len(jobs["jobs"]) == 2

    jobs = hmac_client_team1.get("/api/v1/jobs?limit=2&offset=2").data
    assert len(jobs["jobs"]) == 2

    # if offset is out of bound, the api returns an empty list
    jobs = hmac_client_team1.get("/api/v1/jobs?limit=5&offset=300")
    assert jobs.status_code == 200
    assert jobs.data["jobs"] == []


@mock.patch("dci.api.v1.notifications.job_dispatcher")
def test_get_all_jobs_with_subresources(
    job_dispatcher_mock,
    client_admin,
    hmac_client_team1,
    team1_id,
    team1_remoteci_id,
    rhel_80_component,
    rhel_80_topic_id,
):
    # create 2 jobs and check meta data count
    components = [rhel_80_component["id"]]
    data = {"components": components, "topic_id": rhel_80_topic_id}
    hmac_client_team1.post("/api/v1/jobs", data=data)
    hmac_client_team1.post("/api/v1/jobs", data=data)

    jobs = client_admin.get("/api/v1/jobs").data

    for job in jobs["jobs"]:
        assert "team" in job
        assert job["team"]["id"] == team1_id
        assert job["team_id"] == job["team"]["id"]
        assert "remoteci" in job
        assert job["remoteci"]["id"] == team1_remoteci_id
        assert job["remoteci_id"] == job["remoteci"]["id"]
        assert "team" in job
        assert "results" in job
        assert "components" in job
        cur_set = set(i["id"] for i in job["components"])
        assert cur_set == set(components)

    assert jobs["_meta"]["count"] == 2
    assert len(jobs["jobs"]) == 2
    jobs = client_admin.get("/api/v1/jobs").data
    for job in jobs["jobs"]:
        headers = {
            "DCI-JOB-ID": job["id"],
            "DCI-NAME": "name1.xml",
            "DCI-MIME": "application/junit",
            "Content-Type": "application/junit",
        }
        client_admin.post("/api/v1/files", headers=headers, data=JUNIT)
    jobs = client_admin.get("/api/v1/jobs").data
    assert jobs["_meta"]["count"] == 2
    assert len(jobs["jobs"]) == 2
    for job in jobs["jobs"]:
        assert len(job["results"]) == 1
        for result in job["results"]:
            assert "tests_cases" not in result


def test_get_all_jobs_with_duplicated_embed(
    hmac_client_team1, rhel_80_topic, rhel_80_component_id
):
    data = {"topic_id": rhel_80_topic["id"], "components": [rhel_80_component_id]}
    hmac_client_team1.post("/api/v1/jobs", data=data)
    query_embed = "/api/v1/jobs?embed=" "topic,components," "files,topic,team,remoteci"
    jobs = hmac_client_team1.get(query_embed).data
    assert len(jobs["jobs"]) == 1
    assert len(jobs["jobs"][0]["components"]) == 1
    assert "topic" in jobs["jobs"][0]
    assert "remoteci" in jobs["jobs"][0]


def test_get_all_jobs_with_embed_and_limit(
    hmac_client_team1, rhel_80_topic, rhel_80_component_id
):
    # create 2 jobs and check meta data count
    data = {"topic_id": rhel_80_topic["id"], "components": [rhel_80_component_id]}
    hmac_client_team1.post("/api/v1/jobs", data=data)
    hmac_client_team1.post("/api/v1/jobs", data=data)

    # verify embed with all embedded options
    query_embed = "/api/v1/jobs?embed=components&limit=1&offset=0"
    jobs = hmac_client_team1.get(query_embed).data

    assert len(jobs["jobs"]) == 1
    assert len(jobs["jobs"][0]["components"]) == 1


def test_update_job(client_admin, team1_job_id):
    data_update = {
        "status": "failure",
        "comment": "bar",
        "status_reason": "lol",
        "url": "http://example2.com",
    }

    res = client_admin.get("/api/v1/jobs/%s" % team1_job_id)
    job = res.data["job"]

    res = client_admin.put(
        "/api/v1/jobs/%s" % team1_job_id,
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


def test_success_update_job_status(client_admin, team1_job_id):
    job = client_admin.get("/api/v1/jobs/%s" % team1_job_id)
    job = job.data["job"]

    assert job["status"] == "new"

    data_update = {"status": "pre-run"}
    job = client_admin.put(
        "/api/v1/jobs/%s" % team1_job_id,
        data=data_update,
        headers={"If-match": job["etag"]},
    )
    job = client_admin.get("/api/v1/jobs/%s" % team1_job_id).data["job"]

    assert job["status"] == "pre-run"

    data_update = {"status": "failure"}
    job = client_admin.put(
        "/api/v1/jobs/%s" % team1_job_id,
        data=data_update,
        headers={"If-match": job["etag"]},
    )
    job = client_admin.get("/api/v1/jobs/%s" % team1_job_id).data["job"]

    assert job["status"] == "failure"


def test_job_duration(session, client_admin, team1_job_id):
    job = client_admin.get("/api/v1/jobs/%s" % team1_job_id)
    job = job.data["job"]
    assert job["status"] == "new"
    # update the job with a created_at 5 seconds in the past
    job = session.query(models2.Job).filter(models2.Job.id == team1_job_id).one()
    job.created_at = datetime.datetime.utcnow() - datetime.timedelta(0, 5)
    session.commit()

    data = {"job_id": team1_job_id, "status": "running"}
    js = client_admin.post("/api/v1/jobstates", data=data)
    assert js.status_code == 201
    job = client_admin.get("/api/v1/jobs/%s" % team1_job_id)
    # check those 5 seconds
    assert job.data["job"]["duration"] >= 5


def test_first_job_duration(
    client_admin, team1_job_id, rhel_80_topic, hmac_client_team1
):
    job = client_admin.get("/api/v1/jobs/%s" % team1_job_id).data["job"]
    assert job["duration"] == 0

    job = hmac_client_team1.post(
        "/api/v1/jobs/schedule", data={"topic_id": rhel_80_topic["id"]}
    ).data["job"]
    assert job["duration"] == 0
    job = client_admin.get("/api/v1/jobs/%s" % job["id"]).data["job"]
    assert job["duration"] == 0


def test_get_all_jobs_with_where(client_admin, team1_id, team1_job_id):
    db_job = client_admin.get("/api/v1/jobs?where=id:%s" % team1_job_id).data
    db_job_id = db_job["jobs"][0]["id"]
    assert db_job_id == team1_job_id

    db_job = client_admin.get("/api/v1/jobs?where=team_id:%s" % team1_id).data
    db_job_id = db_job["jobs"][0]["id"]
    assert db_job_id == team1_job_id

    db_job = client_admin.get(
        "/api/v1/jobs?where=id:%s,team_id:%s" % (team1_job_id, team1_id)
    ).data
    db_job_id = db_job["jobs"][0]["id"]
    assert db_job_id == team1_job_id


def test_get_all_jobs_with_pipeline(
    hmac_client_team1, client_user1, team1_id, rhel_80_topic_id
):
    pipeline = client_user1.post(
        "/api/v1/pipelines",
        data={"name": "pipeline1", "team_id": team1_id},
    )
    pipeline_id = pipeline.data["pipeline"]["id"]
    hmac_client_team1.post(
        "/api/v1/jobs/schedule",
        data={"pipeline_id": pipeline_id, "topic_id": rhel_80_topic_id},
    )
    hmac_client_team1.post(
        "/api/v1/jobs/schedule",
        data={"pipeline_id": pipeline_id, "topic_id": rhel_80_topic_id},
    )

    jobs = client_user1.get("/api/v1/jobs").data["jobs"]
    for j in jobs:
        assert "pipeline" in j
        assert j["pipeline"]["name"] == "pipeline1"


def test_where_invalid(client_admin):
    err = client_admin.get("/api/v1/jobs?where=id")

    assert err.status_code == 400
    assert err.data["message"] == "Request malformed"
    assert err.data["payload"]["error"] == "where: 'id' is not a 'key value csv'"


def test_get_all_jobs_with_sort(
    hmac_client_team1, rhel_80_topic_id, rhel_80_component_id
):
    # create 3 jobs ordered by created time
    data = {"components": [rhel_80_component_id], "topic_id": rhel_80_topic_id}
    job_1 = hmac_client_team1.post("/api/v1/jobs", data=data).data["job"]
    job_1.pop("data")
    job_2 = hmac_client_team1.post("/api/v1/jobs", data=data).data["job"]
    job_2.pop("data")
    job_3 = hmac_client_team1.post("/api/v1/jobs", data=data).data["job"]
    job_3.pop("data")

    jobs = hmac_client_team1.get("/api/v1/jobs?sort=created_at").data
    assert jobs["jobs"][0]["id"] == job_1["id"]
    assert jobs["jobs"][1]["id"] == job_2["id"]
    assert jobs["jobs"][2]["id"] == job_3["id"]

    # reverse order by created_at
    jobs = hmac_client_team1.get("/api/v1/jobs?sort=-created_at").data
    assert jobs["jobs"][0]["id"] == job_3["id"]
    assert jobs["jobs"][1]["id"] == job_2["id"]
    assert jobs["jobs"][2]["id"] == job_1["id"]


def test_get_jobs_by_product(client_user1, rhel_product):
    jobs = client_user1.get(
        "/api/v1/jobs?where=product_id:%s" % rhel_product["id"]
    ).data["jobs"]
    for job in jobs:
        assert job["product_id"] == rhel_product["id"]


def test_get_job_by_id(hmac_client_team1, rhel_80_topic_id, rhel_80_component_id):
    job = hmac_client_team1.post(
        "/api/v1/jobs",
        data={"components": [rhel_80_component_id], "topic_id": rhel_80_topic_id},
    )
    job_id = job.data["job"]["id"]

    job = hmac_client_team1.get("/api/v1/jobs/%s" % job_id)
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


def test_get_jobstates_by_job_id(client_admin, client_user1, team1_job_id):
    data = {"status": "new", "job_id": team1_job_id}
    jobstate_ids = set(
        [
            client_admin.post("/api/v1/jobstates", data=data).data["jobstate"]["id"],
            client_admin.post("/api/v1/jobstates", data=data).data["jobstate"]["id"],
        ]
    )

    jobstates = client_user1.get("/api/v1/jobs/%s/jobstates" % team1_job_id)
    assert jobstates.status_code == 200
    jobstates = jobstates.data["jobstates"]

    found_jobstate_ids = set(i["id"] for i in jobstates)
    assert jobstate_ids == found_jobstate_ids

    # verify embed with all embedded options
    jobstates = client_admin.get("/api/v1/jobs/%s?embed=jobstates" % team1_job_id)
    assert len(jobstates.data["job"]["jobstates"]) == len(found_jobstate_ids)


def test_get_jobstates_by_job_id_sorted(
    client_admin, client_user1, team1_job_id, session
):
    data = {"status": "new", "job_id": team1_job_id}
    jobstate_ids = [
        client_admin.post("/api/v1/jobstates", data=data).data["jobstate"]["id"],
        client_admin.post("/api/v1/jobstates", data=data).data["jobstate"]["id"],
        client_admin.post("/api/v1/jobstates", data=data).data["jobstate"]["id"],
    ]

    job = client_user1.get("/api/v1/jobs/%s" % team1_job_id)
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

    job = client_user1.get("/api/v1/jobs/%s" % team1_job_id)
    assert job.status_code == 200
    assert jobstate_ids[2] == job.data["job"]["jobstates"][0]["id"]
    assert jobstate_ids[0] == job.data["job"]["jobstates"][1]["id"]
    assert jobstate_ids[1] == job.data["job"]["jobstates"][2]["id"]


def test_get_jobstates_by_job_id_by_epm(client_epm, client_admin, team1_job_id):
    data = {"status": "new", "job_id": team1_job_id}
    jobstate_ids = set(
        [
            client_admin.post("/api/v1/jobstates", data=data).data["jobstate"]["id"],
            client_admin.post("/api/v1/jobstates", data=data).data["jobstate"]["id"],
        ]
    )

    jobstates = client_epm.get("/api/v1/jobs/%s/jobstates" % team1_job_id)
    assert jobstates.status_code == 200
    jobstates = jobstates.data["jobstates"]

    found_jobstate_ids = set(i["id"] for i in jobstates)
    assert jobstate_ids == found_jobstate_ids

    # verify embed with all embedded options
    jobstates = client_admin.get("/api/v1/jobs/%s?embed=jobstates" % team1_job_id)
    assert len(jobstates.data["job"]["jobstates"]) == len(found_jobstate_ids)


def test_get_jobstates_by_job_id_with_embed(client_admin, team1_job_id, team1_jobstate):
    with mock.patch(AWSS3, spec=S3) as mock_s3:
        mockito = mock.MagicMock()

        head_result = {
            "etag": utils.gen_etag(),
            "content-type": "stream",
            "content-length": 7,
        }

        mockito.head.return_value = head_result
        mock_s3.return_value = mockito
        headers = {"DCI-JOBSTATE-ID": team1_jobstate, "DCI-NAME": "name1"}
        pfile = client_admin.post(
            "/api/v1/files", headers=headers, data="kikoolol"
        ).data
        file1_id = pfile["file"]["id"]
        headers = {"DCI-JOBSTATE-ID": team1_jobstate, "DCI-NAME": "name2"}
        pfile = client_admin.post(
            "/api/v1/files", headers=headers, data="kikoolol"
        ).data
        file2_id = pfile["file"]["id"]
        jobstates = client_admin.get(
            "/api/v1/jobs/%s/jobstates" "?embed=files" % team1_job_id
        )
        jobstate = jobstates.data["jobstates"][0]
        assert set((jobstate["files"][0]["id"], jobstate["files"][1]["id"])) == set(
            (file1_id, file2_id)
        )


def test_get_job_not_found(client_admin):
    result = client_admin.get("/api/v1/jobs/%s" % uuid.uuid4())
    assert result.status_code == 404


def test_get_jobs_with_schedule(hmac_client_team1, rhel_80_topic_id, rhel_80_component):
    # schedule a job
    data = {"topic_id": rhel_80_topic_id, "comment": "kikoolol"}
    job = hmac_client_team1.post("/api/v1/jobs/schedule", data=data)
    assert job.status_code == 201
    job_id = job.data["job"]["id"]
    assert job.data["job"]["comment"] == "kikoolol"

    # get the components of the scheduled jobs
    job_components = hmac_client_team1.get("/api/v1/jobs/%s/components" % job_id).data
    for c in job_components["components"]:
        url = "/api/v1/components/%s?embed=jobs" % c["id"]
        component = hmac_client_team1.get(url).data
        assert component["component"]["jobs"][0]["id"] == job_id


def test_delete_job_by_id(hmac_client_team1, rhel_80_topic_id, rhel_80_component_id):
    job = hmac_client_team1.post(
        "/api/v1/jobs",
        data={"components": [rhel_80_component_id], "topic_id": rhel_80_topic_id},
    )
    job_id = job.data["job"]["id"]
    job_etag = job.headers.get("ETag")
    assert job.status_code == 201

    job = hmac_client_team1.get("/api/v1/jobs/%s" % job_id)
    assert job.status_code == 200

    deleted_job = hmac_client_team1.delete(
        "/api/v1/jobs/%s" % job_id, headers={"If-match": job_etag}
    )
    assert deleted_job.status_code == 204

    job = hmac_client_team1.get("/api/v1/jobs/%s" % job_id)
    assert job.status_code == 404


def test_delete_job_archive_dependencies(client_admin, team1_job_id):
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
            "DCI-JOB-ID": team1_job_id,
            "DCI-NAME": "afile.txt",
            "Content-Type": "text/plain",
        }

        file = client_admin.post("/api/v1/files", headers=headers, data="content")
        assert file.status_code == 201

        url = "/api/v1/jobs/%s" % team1_job_id
        job = client_admin.get(url)
        etag = job.data["job"]["etag"]
        assert job.status_code == 200

        deleted_job = client_admin.delete(url, headers={"If-match": etag})
        assert deleted_job.status_code == 204

        url = "/api/v1/files/%s" % file.data["file"]["id"]
        file = client_admin.get(url)
        assert file.status_code == 404


# Tests for the isolation


def test_get_all_jobs_as_user(client_user1, team1_id, team1_job_id):
    jobs = client_user1.get("/api/v1/jobs")
    assert jobs.status_code == 200
    assert jobs.data["_meta"]["count"] == 1
    for job in jobs.data["jobs"]:
        assert job["team_id"] == team1_id


def test_get_all_jobs_as_epm(client_epm, team1_id, team1_job_id):
    jobs = client_epm.get("/api/v1/jobs")
    assert jobs.status_code == 200
    assert jobs.data["_meta"]["count"] == 1
    for job in jobs.data["jobs"]:
        assert job["team_id"] == team1_id


def test_get_job_as_user(
    client_user1, hmac_client_team1, rhel_80_topic_id, rhel_80_component_id
):
    job = hmac_client_team1.post(
        "/api/v1/jobs",
        data={"components": [rhel_80_component_id], "topic_id": rhel_80_topic_id},
    ).data
    job_id = job["job"]["id"]
    job = client_user1.get("/api/v1/jobs/%s" % job_id)
    assert job.status_code == 200


def test_delete_job_as_user(client_user1, team1_job_id):
    job = client_user1.get("/api/v1/jobs/%s" % team1_job_id)
    job_etag = job.headers.get("ETag")

    job_delete = client_user1.delete(
        "/api/v1/jobs/%s" % team1_job_id, headers={"If-match": job_etag}
    )

    assert job_delete.status_code == 204

    job = client_user1.get("/api/v1/jobs/%s" % team1_job_id)
    assert job.status_code == 404


def test_nrt_delete_job_as_user_and_red_hat(
    client_admin, team_redhat_id, user1_id, client_user1, team1_job_id
):
    add_user_in_redhat_team = client_admin.post(
        "/api/v1/teams/%s/users/%s" % (team_redhat_id, user1_id), data={}
    )
    assert add_user_in_redhat_team.status_code == 201

    job = client_user1.get("/api/v1/jobs/%s" % team1_job_id)
    job_etag = job.headers.get("ETag")
    job_delete = client_user1.delete(
        "/api/v1/jobs/%s" % team1_job_id, headers={"If-match": job_etag}
    )
    assert job_delete.status_code == 204
    job = client_user1.get("/api/v1/jobs/%s" % team1_job_id)
    assert job.status_code == 404


def test_when_a_user_delete_a_job_we_add_log_entry(
    session, client_user1, user1_id, team1_job_id
):
    job = client_user1.get("/api/v1/jobs/%s" % team1_job_id)
    job_etag = job.headers.get("ETag")

    job_delete = client_user1.delete(
        "/api/v1/jobs/%s" % team1_job_id, headers={"If-match": job_etag}
    )
    assert job_delete.status_code == 204

    logs = session.query(models2.Log).all()
    assert len(logs) == 1
    assert str(logs[0].user_id) == user1_id
    assert logs[0].action == "delete_job_by_id"


def test_create_file_for_job_id(
    client_user1, hmac_client_team1, rhel_80_topic_id, rhel_80_component_id
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
        job = hmac_client_team1.post(
            "/api/v1/jobs",
            data={
                "components": [rhel_80_component_id],
                "topic_id": rhel_80_topic_id,
            },
        )
        job_id = job.data["job"]["id"]
        assert job.status_code == 201

        # create a file
        headers = {"DCI-JOB-ID": job_id, "DCI-NAME": "foobar"}
        file = client_user1.post("/api/v1/files", headers=headers)
        file_id = file.data["file"]["id"]
        file = client_user1.get("/api/v1/files/%s" % file_id).data
        assert file["file"]["name"] == "foobar"


def test_get_files_by_job_id(client_user1, team1_job_id, team1_job_file):
    # get files from job
    file_from_job = client_user1.get("/api/v1/jobs/%s/files" % team1_job_id)
    assert file_from_job.status_code == 200
    assert file_from_job.data["_meta"]["count"] == 1


def test_get_files_by_job_id_as_epm(client_epm, team1_job_id, team1_job_file):
    # get files from job
    file_from_job = client_epm.get("/api/v1/jobs/%s/files" % team1_job_id)
    assert file_from_job.status_code == 200
    assert file_from_job.data["_meta"]["count"] == 1


@mock.patch("dci.api.v1.notifications.job_dispatcher")
def test_get_results_by_job_id(job_dispatcher_mock, client_user1, team1_job_id):
    headers = {
        "DCI-JOB-ID": team1_job_id,
        "Content-Type": "application/junit",
        "DCI-MIME": "application/junit",
        "DCI-NAME": "res_junit.xml",
    }

    client_user1.post("/api/v1/files", headers=headers, data=JUNIT)

    # get file from job
    file_from_job = client_user1.get("/api/v1/jobs/%s/results" % team1_job_id)
    assert file_from_job.status_code == 200
    assert file_from_job.data["_meta"]["count"] == 1
    assert file_from_job.data["results"][0]["total"] == 6


def test_purge(client_user1, client_admin, team1_job_id, team1_id):
    file_id1 = t_utils.create_file(client_user1, team1_job_id, "kikoolol", "content")[
        "id"
    ]
    job = client_user1.get("/api/v1/jobs/%s" % team1_job_id).data["job"]

    djob = client_admin.delete(
        "/api/v1/jobs/%s" % team1_job_id, headers={"If-match": job["etag"]}
    )
    assert djob.status_code == 204
    to_purge_jobs = client_admin.get("/api/v1/jobs/purge").data
    assert len(to_purge_jobs["jobs"]) == 1
    to_purge_files = client_admin.get("/api/v1/files/purge").data
    assert len(to_purge_files["files"]) == 1

    client_admin.post("/api/v1/jobs/purge")
    path1 = files_utils.build_file_path(team1_id, team1_job_id, file_id1)
    store = dci_config.get_store()
    # the purge removed the file from the backend, get() must raise exception
    with pytest.raises(dci_exc.StoreException):
        store.get("files", path1)

    client_admin.post("/api/v1/jobs/purge")
    to_purge_jobs = client_admin.get("/api/v1/jobs/purge").data
    assert len(to_purge_jobs["jobs"]) == 0
    to_purge_files = client_admin.get("/api/v1/files/purge").data
    assert len(to_purge_files["files"]) == 0


def test_purge_failure(client_user1, client_admin, team1_job_id, team1_id):
    file_id1 = t_utils.create_file(client_user1, team1_job_id, "kikoolol", "content")[
        "id"
    ]
    job = client_user1.get("/api/v1/jobs/%s" % team1_job_id).data["job"]

    djob = client_admin.delete(
        "/api/v1/jobs/%s" % team1_job_id, headers={"If-match": job["etag"]}
    )
    assert djob.status_code == 204
    to_purge_jobs = client_admin.get("/api/v1/jobs/purge").data
    assert len(to_purge_jobs["jobs"]) == 1
    to_purge_files = client_admin.get("/api/v1/files/purge").data
    assert len(to_purge_files["files"]) == 1

    # purge will fail
    with mock.patch("dci.stores.s3.S3.delete") as mock_delete:
        mock_delete.side_effect = dci_exc.StoreException("error")
        purge_res = client_admin.post("/api/v1/jobs/purge")
        assert purge_res.status_code == 400
        path1 = files_utils.build_file_path(team1_id, team1_job_id, file_id1)
        store = dci_config.get_store()
        # because the delete fail the backend didn't remove the files and the
        # files are still in the database
        store.get("files", path1)
    to_purge_files = client_admin.get("/api/v1/files/purge").data
    assert len(to_purge_files["files"]) == 1
    to_purge_jobs = client_admin.get("/api/v1/jobs/purge").data
    assert len(to_purge_jobs["jobs"]) == 1


def test_nrt_get_then_put_on_job_with_no_error(client_user1, team1_job_id):
    r = client_user1.get("/api/v1/jobs/%s" % team1_job_id)
    assert r.status_code == 200
    job = r.data["job"]
    r = client_user1.put(
        "/api/v1/jobs/%s" % team1_job_id,
        data=job,
        headers={"If-match": job["etag"]},
    )
    assert r.status_code == 200
