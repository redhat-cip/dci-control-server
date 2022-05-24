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


def test_create_and_get_pipeline(user, team_user_id):
    pipeline = user.post(
        "/api/v1/pipelines",
        data={"name": "pipeline1", "team_id": team_user_id},
    )
    assert pipeline.status_code == 201
    pipeline_id = pipeline.data["pipeline"]["id"]

    get_pipeline = user.get("/api/v1/pipelines/%s" % pipeline_id)
    assert get_pipeline.status_code == 200
    get_pipeline = get_pipeline.data["pipeline"]
    assert get_pipeline["id"] == pipeline_id
    assert get_pipeline["name"] == "pipeline1"


def test_jobs_schedule_with_pipeline(
    remoteci_context, user, team_user_id, topic_user_id
):
    pipeline = user.post(
        "/api/v1/pipelines",
        data={"name": "pipeline1", "team_id": team_user_id},
    )
    pipeline_id = pipeline.data["pipeline"]["id"]
    job_1 = remoteci_context.post(
        "/api/v1/jobs/schedule",
        data={"pipeline_id": pipeline_id, "topic_id": topic_user_id},
    )
    assert job_1.status_code == 201
    assert job_1.data["job"]["pipeline_id"] == pipeline_id
    job_1 = job_1.data["job"]

    job_2 = remoteci_context.post(
        "/api/v1/jobs/schedule",
        data={"pipeline_id": pipeline_id, "topic_id": topic_user_id},
    )
    assert job_2.status_code == 201
    assert job_2.data["job"]["pipeline_id"] == pipeline_id
    job_2 = job_2.data["job"]

    jobs_pipeline = remoteci_context.get("/api/v1/pipelines/%s/jobs" % pipeline_id)
    jobs_pipeline = jobs_pipeline.data["jobs"]
    assert jobs_pipeline[0]["id"] == job_1["id"]
    assert jobs_pipeline[1]["id"] == job_2["id"]


def test_jobs_create_with_pipeline(
    remoteci_context, user, team_user_id, topic_user_id, components_ids
):
    pipeline = user.post(
        "/api/v1/pipelines",
        data={"name": "pipeline1", "team_id": team_user_id},
    )
    pipeline_id = pipeline.data["pipeline"]["id"]
    job_1 = remoteci_context.post(
        "/api/v1/jobs",
        data={
            "pipeline_id": pipeline_id,
            "topic_id": topic_user_id,
            "components": components_ids,
        },
    )
    assert job_1.status_code == 201
    assert job_1.data["job"]["pipeline_id"] == pipeline_id
    job_1 = job_1.data["job"]

    job_2 = remoteci_context.post(
        "/api/v1/jobs",
        data={
            "pipeline_id": pipeline_id,
            "topic_id": topic_user_id,
            "components": components_ids,
        },
    )
    assert job_2.status_code == 201
    assert job_2.data["job"]["pipeline_id"] == pipeline_id
    job_2 = job_2.data["job"]

    jobs_pipeline = remoteci_context.get("/api/v1/pipelines/%s/jobs" % pipeline_id)
    jobs_pipeline = jobs_pipeline.data["jobs"]
    assert jobs_pipeline[0]["id"] == job_1["id"]
    assert jobs_pipeline[1]["id"] == job_2["id"]


def test_get_pipelines(remoteci_context, team_user_id):
    for _ in range(3):
        pipeline = remoteci_context.post(
            "/api/v1/pipelines",
            data={
                "name": "pipeline1",
                "team_id": team_user_id,
            },
        )
        assert pipeline.status_code == 201

    pipelines = remoteci_context.get("/api/v1/pipelines")
    assert len(pipelines.data["pipelines"]) == 3


def test_update_pipeline(user, remoteci_context, team_user_id):
    pipeline = remoteci_context.post(
        "/api/v1/pipelines",
        data={"name": "pipeline1", "team_id": team_user_id},
    )
    pipeline_id = pipeline.data["pipeline"]["id"]
    pipeline_etag = pipeline.data["pipeline"]["etag"]
    assert pipeline.status_code == 201

    updates = {"name": "pipeline2"}
    update_pipeline = remoteci_context.put(
        "/api/v1/pipelines/%s" % pipeline_id,
        headers={"If-match": pipeline_etag},
        data=updates,
    )
    assert update_pipeline.status_code == 200

    get_pipeline = user.get("/api/v1/pipelines/%s" % pipeline_id)
    assert get_pipeline.status_code == 200
    get_pipeline = get_pipeline.data["pipeline"]
    assert get_pipeline["name"] == "pipeline2"


def test_delete_pipeline(remoteci_context, team_user_id):
    pipeline = remoteci_context.post(
        "/api/v1/pipelines",
        data={"name": "pipeline1", "team_id": team_user_id},
    )
    pipeline_id = pipeline.data["pipeline"]["id"]
    pipeline_etag = pipeline.data["pipeline"]["etag"]
    assert pipeline.status_code == 201

    delete_pipeline = remoteci_context.delete(
        "/api/v1/pipelines/%s" % pipeline_id, headers={"If-match": pipeline_etag}
    )
    assert delete_pipeline.status_code == 204

    get_pipeline = remoteci_context.get("/api/v1/pipelines/%s" % pipeline_id)
    assert get_pipeline.status_code == 404


# Permission test suites


def test_get_pipeline_not_authorized(
    user,
    user2,
    team_user_id,
):
    pipeline = user.post(
        "/api/v1/pipelines",
        data={"name": "pipeline1", "team_id": team_user_id},
    )
    assert pipeline.status_code == 201
    pipeline_id = pipeline.data["pipeline"]["id"]

    get_pipeline = user.get("/api/v1/pipelines/%s" % pipeline_id)
    assert get_pipeline.status_code == 200

    get_pipeline = user2.get("/api/v1/pipelines/%s" % pipeline_id)
    assert get_pipeline.status_code == 401


def test_jobs_from_pipeline_not_authorized(
    remoteci_context, user, team_user_id, topic_user_id, user2
):
    pipeline = user.post(
        "/api/v1/pipelines",
        data={"name": "pipeline1", "team_id": team_user_id},
    )
    pipeline_id = pipeline.data["pipeline"]["id"]
    job = remoteci_context.post(
        "/api/v1/jobs/schedule",
        data={"pipeline_id": pipeline_id, "topic_id": topic_user_id},
    )
    assert job.status_code == 201
    get_pipeline = user2.get("/api/v1/pipelines/%s/jobs" % pipeline_id)
    assert get_pipeline.status_code == 401


def test_create_pipeline_for_another_team_not_authorized(user, team_user_id2):
    pipeline = user.post(
        "/api/v1/pipelines",
        data={"name": "pipeline1", "team_id": team_user_id2},
    )
    assert pipeline.status_code == 401
