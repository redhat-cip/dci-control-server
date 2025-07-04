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

from __future__ import unicode_literals

import base64

import flask
import mock
import pytest

from datetime import datetime
from datetime import timedelta
from uuid import UUID
from sqlalchemy import sql

from dci import dci_config
from dci.api.v1 import files
from dci.common import exceptions as dci_exc
from dci.db import models2
from dci.stores import files_utils
from tests import data as tests_data
from tests import utils as t_utils


def test_create_files(client_user1, team1_jobstate):
    file_id = t_utils.create_task_file(client_user1, team1_jobstate, "file", "content")[
        "id"
    ]

    file = client_user1.get("/api/v1/files/%s" % file_id).data["file"]

    assert file["name"] == "file"
    assert file["size"] == 7


def test_job_update_on_creation_deletion_file(client_user1, team1_job_id):
    job = client_user1.get("/api/v1/jobs/%s" % team1_job_id).data["job"]
    job_updated_at = job["updated_at"]

    file_id = t_utils.create_file(
        client_user1, team1_job_id, "name", content="c", content_type="text/plain"
    )["id"]

    job = client_user1.get("/api/v1/jobs/%s" % team1_job_id).data["job"]
    assert job_updated_at != job["updated_at"]

    job_updated_at = job["updated_at"]

    client_user1.delete("/api/v1/files/%s" % str(file_id))

    job = client_user1.get("/api/v1/jobs/%s" % team1_job_id).data["job"]
    assert job_updated_at != job["updated_at"]


def test_create_files_jobstate_id_and_job_id_missing(client_admin):
    file = client_admin.post(
        "/api/v1/files", headers={"DCI-NAME": "file"}, data="content"
    )
    assert file.status_code == 400


@mock.patch("dci.common.time.datetime")
def test_create_task_file_update_job_duration(m_datetime_j, client_user1, team1_job):
    job_created_at = team1_job["created_at"]
    d_j_created_at = datetime.strptime(job_created_at, "%Y-%m-%dT%H:%M:%S.%f")

    # check jobstate creation updating job duration
    m_datetime_j.datetime.utcnow.return_value = d_j_created_at + timedelta(
        seconds=86405
    )
    data = {"job_id": team1_job["id"], "status": "running"}
    jobstate = client_user1.post("/api/v1/jobstates", data=data).data["jobstate"]
    team1_job = client_user1.get("/api/v1/jobs/%s" % team1_job["id"]).data["job"]
    assert team1_job["duration"] == 86405

    # check task file creation update job duration
    m_datetime_j.datetime.utcnow.return_value = d_j_created_at + timedelta(
        seconds=86410
    )
    t_utils.create_task_file(
        client_user1,
        jobstate["id"],
        "Rally",
        tests_data.jobtest_one,
        "ansible/output",
    )
    team1_job = client_user1.get("/api/v1/jobs/%s" % team1_job["id"]).data["job"]
    assert team1_job["duration"] == 86410


@mock.patch("dci.api.v1.notifications.job_dispatcher")
def test_upload_tests_with_regressions_successfix(
    mocked_disp, client_admin, hmac_client_team1, rhel_80_topic, rhel_80_component_id
):
    headers = {
        "User-Agent": "python-dciclient",
        "Client-Version": "python-dciclient_0.1.0",
    }

    # 1. schedule two jobs and create their files
    data = {
        "topic_id": rhel_80_topic["id"],
        "components_ids": [rhel_80_component_id],
    }
    job_1 = hmac_client_team1.post(
        "/api/v1/jobs/schedule", headers=headers, data=data
    ).data["job"]
    job_2 = hmac_client_team1.post(
        "/api/v1/jobs/schedule", headers=headers, data=data
    ).data["job"]

    f_1 = t_utils.create_file(
        client_admin,
        job_1["id"],
        "Tempest",
        tests_data.jobtest_one,
        "application/junit",
    )["id"]
    assert f_1 is not None
    t_utils.create_file(
        client_admin,
        job_1["id"],
        "Rally",
        tests_data.jobtest_one,
        "application/junit",
    )

    f_2 = t_utils.create_file(
        client_admin,
        job_2["id"],
        "Tempest",
        tests_data.jobtest_two,
        "application/junit",
    )["id"]
    assert f_2 is not None
    t_utils.create_file(
        client_admin,
        job_2["id"],
        "Rally",
        tests_data.jobtest_one,
        "application/junit",
    )

    # 3. verify regression in job_2's result which is 'test_3'
    job_2_results = client_admin.get(
        "/api/v1/jobs/%s?embed=results" % job_2["id"]
    ).data["job"]["results"]

    for job_res in job_2_results:
        if job_res["name"] == "Tempest":
            assert job_res["regressions"] == 1
            assert job_res["successfixes"] == 1
        elif job_res["name"] == "Rally":
            assert job_res["regressions"] == 0
            assert job_res["successfixes"] == 0


def test_get_file_by_id(client_user1, team1_job_id):
    file_id = t_utils.create_file(client_user1, team1_job_id, "file")["id"]

    # get by uuid
    created_file = client_user1.get("/api/v1/files/%s" % file_id)
    assert created_file.status_code == 200
    assert created_file.data["file"]["name"] == "file"


def test_get_file_not_found(client_user1):
    result = client_user1.get("/api/v1/files/ptdr")
    assert result.status_code == 404


def test_delete_file_by_id(client_user1, team1_job_id):
    file_id = t_utils.create_file(client_user1, team1_job_id, "name")["id"]
    url = "/api/v1/files/%s" % file_id

    created_file = client_user1.get(url)
    assert created_file.status_code == 200

    deleted_file = client_user1.delete(url)
    assert deleted_file.status_code == 204

    gfile = client_user1.get(url)
    assert gfile.status_code == 404


# Tests for the isolation


def test_create_file_as_user(client_user1, team1_jobstate):
    headers = {"DCI-JOBSTATE-ID": team1_jobstate, "DCI-NAME": "name"}
    file = client_user1.post("/api/v1/files", headers=headers)
    assert file.status_code == 201


def test_get_file_as_user(client_user1, team1_jobstate_file, team1_jobstate):
    file = client_user1.get("/api/v1/files/%s" % team1_jobstate_file)
    assert file.status_code == 200


def test_delete_file_as_user(client_user1, team1_jobstate_file):
    file_delete = client_user1.delete("/api/v1/files/%s" % team1_jobstate_file)
    assert file_delete.status_code == 204


def test_get_file_content_as_user(client_user1, team1_jobstate):
    content = "azertyuiop1234567890"
    file_id = t_utils.create_task_file(client_user1, team1_jobstate, "foo", content)[
        "id"
    ]

    get_file = client_user1.get("/api/v1/files/%s/content" % file_id)

    assert get_file.status_code == 200
    assert get_file.data == content


def test_change_file_to_invalid_state(client_admin, team1_jobstate_file):
    t = client_admin.get("/api/v1/files/" + team1_jobstate_file).data["file"]
    data = {"state": "file"}
    r = client_admin.put(
        "/api/v1/files/" + team1_jobstate_file,
        data=data,
        headers={"If-match": t["etag"]},
    )
    assert r.status_code == 405
    current_file = client_admin.get("/api/v1/files/" + team1_jobstate_file)
    assert current_file.status_code == 200
    assert current_file.data["file"]["state"] == "active"


def test_get_file_info_from_header():
    headers = {
        "DCI-Client-Info": "",
        "DCI-Auth-Signature": "",
        "Authorization": "",
        "DCI-Datetime": "",
        "mime": "",
        "Dci-Job-Id": "",
    }
    file_info = files.get_file_info_from_headers(headers)
    assert len(file_info.keys()) == 2
    assert "mime" in file_info
    assert "job_id" in file_info


def test_build_certification():
    with open("tests/data/certification.xml.tar.gz", "rb") as f:
        node_id = "40167"
        username = "dci"
        password = "dci"
        file_name = "certification.xml.tar.gz"
        file_content = f.read()
        cert = files.build_certification(
            username, password, node_id, file_name, file_content
        )

        assert cert["username"] == "dci"
        assert cert["password"] == "dci"
        assert cert["id"] == "40167"
        assert cert["type"] == "certification"
        assert cert["description"] == "DCI automatic upload test log"
        assert cert["filename"] == "certification.xml.tar.gz"

        base64.decodebytes(cert["data"])


def test_get_previous_job_in_topic(
    app,
    client_user1,
    hmac_client_team1,
    team1_id,
    session,
    rhel_80_topic_id,
    rhel_80_component_id,
):
    def get_new_remoteci_context():
        data = {"name": "rname_new", "team_id": team1_id}
        remoteci = client_user1.post("/api/v1/remotecis", data=data).data
        remoteci_id = str(remoteci["remoteci"]["id"])
        api_secret = client_user1.get("/api/v1/remotecis/%s" % remoteci_id).data
        api_secret = api_secret["remoteci"]["api_secret"]

        remoteci = {"id": remoteci_id, "api_secret": api_secret, "type": "remoteci"}
        return t_utils.generate_token_based_client(app, remoteci)

    # job_1 from remoteci_context
    data = {
        "comment": "file",
        "components": [rhel_80_component_id],
        "team_id": team1_id,
        "topic_id": rhel_80_topic_id,
        "name": "ocp-vanilla",
        "configuration": "cluster-8-nodes-sriov",
    }
    prev_job = hmac_client_team1.post("/api/v1/jobs", data=data).data
    prev_job_id = prev_job["job"]["id"]

    # adding a job in between from a new remoteci
    new_remoteci = get_new_remoteci_context()
    # job_2 from new remoteci
    new_remoteci.post("/api/v1/jobs", data=data)

    # job_3 from remoteci_context
    data["configuration"] = "cluster-5-nodes-sriov"
    data["name"] = "ocp-vanilla-fredco"
    new_job = hmac_client_team1.post("/api/v1/jobs", data=data).data
    new_job = models2.Job(**new_job["job"])

    # job_4 from remoteci_context
    # prev(job_4) must be job_1 and not job_2 nor job_3
    data["configuration"] = "cluster-8-nodes-sriov"
    data["name"] = "ocp-vanilla"
    new_job = hmac_client_team1.post("/api/v1/jobs", data=data).data
    new_job = models2.Job(**new_job["job"])

    with app.app_context():
        flask.g.session = session
        test_prev_job_id = str(files.get_previous_job_in_topic(new_job).id)
        assert prev_job_id == test_prev_job_id


def test_purge(
    client_admin,
    client_user1,
    team1_job_id,
    team1_id,
):
    # create two files and archive them
    file_id1 = t_utils.create_file(client_user1, team1_job_id, "file1", "content1")[
        "id"
    ]
    client_user1.delete("/api/v1/files/%s" % file_id1)
    file_id2 = t_utils.create_file(client_user1, team1_job_id, "file2", "content2")[
        "id"
    ]
    client_user1.delete("/api/v1/files/%s" % file_id2)

    to_purge = client_admin.get("/api/v1/files/purge").data
    assert len(to_purge["files"]) == 2
    client_admin.post("/api/v1/files/purge")
    path1 = files_utils.build_file_path(team1_id, team1_job_id, file_id1)
    store = dci_config.get_store()
    # the purge removed the file from the backend, get() must raise exception
    with pytest.raises(dci_exc.StoreException):
        store.get("files", path1)
    path2 = files_utils.build_file_path(team1_id, team1_job_id, file_id2)
    with pytest.raises(dci_exc.StoreException):
        store.get("files", path2)
    to_purge = client_admin.get("/api/v1/files/purge").data
    assert len(to_purge["files"]) == 0


def test_purge_failure(client_admin, client_user1, team1_job_id, team1_id):
    # create two files and archive them
    file_id1 = t_utils.create_file(client_user1, team1_job_id, "file", "content")["id"]
    client_user1.delete("/api/v1/files/%s" % file_id1)
    file_id2 = t_utils.create_file(client_user1, team1_job_id, "file2", "content2")[
        "id"
    ]
    client_user1.delete("/api/v1/files/%s" % file_id2)

    to_purge = client_admin.get("/api/v1/files/purge").data
    assert len(to_purge["files"]) == 2

    # purge will fail
    with mock.patch("dci.stores.s3.S3.delete") as mock_delete:
        mock_delete.side_effect = dci_exc.StoreException("error")
        purge_res = client_admin.post("/api/v1/files/purge")
        assert purge_res.status_code == 400
        path1 = files_utils.build_file_path(team1_id, team1_job_id, file_id1)
        path2 = files_utils.build_file_path(team1_id, team1_job_id, file_id2)
        store = dci_config.get_store()
        store.get("files", path1)
        store.get("files", path2)
    to_purge = client_admin.get("/api/v1/files/purge").data
    assert len(to_purge["files"]) == 2


@mock.patch("dci.api.v1.notifications.job_dispatcher")
def test_get_junit_file(_, client_user1, team1_job):
    junit_id = t_utils.create_file(
        client_user1,
        team1_job["id"],
        "Tempest",
        tests_data.jobtest_one,
        "application/junit",
    )["id"]
    data = client_user1.get("/api/v1/files/%s/junit" % junit_id).data
    assert len(data["testsuites"]) == 1
    assert data["id"] == junit_id
    assert data["name"] == "Tempest"
    assert data["job"]["id"] == team1_job["id"]
    assert data["job"]["name"] == team1_job["name"]
    assert data["previous_job"] is None
    assert data["testsuites"][0] == {
        "id": 0,
        "additions": 3,
        "deletions": 0,
        "errors": 0,
        "failures": 1,
        "name": "Kikoolol1",
        "skipped": 0,
        "success": 2,
        "successfixes": 0,
        "regressions": 0,
        "properties": [],
        "testcases": [
            {
                "action": "failure",
                "classname": "Testsuite_1",
                "message": None,
                "name": "test_1",
                "properties": [],
                "state": "ADDED",
                "stderr": None,
                "stdout": None,
                "time": 30.0,
                "type": "Exception",
                "value": "Traceback",
                "successfix": False,
                "regression": False,
            },
            {
                "action": "success",
                "classname": "Testsuite_1",
                "message": None,
                "name": "test_2",
                "properties": [],
                "state": "ADDED",
                "stderr": None,
                "stdout": None,
                "time": 40.0,
                "type": None,
                "value": "",
                "successfix": False,
                "regression": False,
            },
            {
                "action": "success",
                "classname": "Testsuite_1",
                "message": None,
                "name": "test_3[id-2fc6822e-b5a8-42ed-967b-11d86e881ce3,smoke]",
                "properties": [],
                "state": "ADDED",
                "stderr": None,
                "stdout": None,
                "time": 40.0,
                "type": None,
                "value": "",
                "successfix": False,
                "regression": False,
            },
        ],
        "tests": 3,
        "time": 110.0,
        "unchanged": 0,
    }


def test_nrt_dont_returned_deleted_files_in_get_job(client_user1, team1_job_id):
    file1 = t_utils.create_file(client_user1, team1_job_id, "file1", "content1")
    client_user1.delete("/api/v1/files/%s" % file1["id"])
    file2 = t_utils.create_file(client_user1, team1_job_id, "file2", "content2")
    job = client_user1.get("/api/v1/jobs/%s" % team1_job_id).data["job"]
    assert len(job["files"]) == 1
    assert job["files"][0]["id"] == file2["id"]


@mock.patch("dci.api.v1.notifications.job_dispatcher")
def test_nrt_get_an_empty_junit_file(_, client_user1, team1_job_id):
    content = ""
    junit_id = t_utils.create_file(
        client_user1,
        team1_job_id,
        "Tempest",
        content,
        "application/junit",
    )["id"]
    testsuites = client_user1.get("/api/v1/files/%s/junit" % junit_id).data[
        "testsuites"
    ]
    assert len(testsuites) == 0


@mock.patch("dci.api.v1.notifications.job_dispatcher")
def test_retrieve_junit(job_dispatcher_mock, client_admin, team1_job_id):
    headers = {
        "DCI-NAME": "junit_file.xml",
        "DCI-JOB-ID": team1_job_id,
        "DCI-MIME": "application/junit",
        "Content-Disposition": "attachment; filename=junit_file.xml",
        "Content-Type": "application/junit",
    }

    file = client_admin.post("/api/v1/files", headers=headers, data=tests_data.JUNIT)
    file_id = file.data["file"]["id"]

    # First retrieve file
    res = client_admin.get("/api/v1/files/%s/content" % file_id)

    assert res.data == tests_data.JUNIT

    # Non Regression Test: XHR doesn't modify content
    headers = {"X-Requested-With": "XMLHttpRequest"}
    res = client_admin.get("/api/v1/files/%s/content" % file_id, headers=headers)

    assert res.data == tests_data.JUNIT
    assert res.headers["Content-Type"] == "application/junit"


@mock.patch("dci.api.v1.notifications.job_dispatcher")
def test_create_file_fill_tests_results_table(
    job_dispatcher_mock, engine, client_admin, team1_job_id
):
    with open("tests/data/tempest-results.xml", "r") as f:
        content_file = f.read()

    headers = {
        "DCI-JOB-ID": team1_job_id,
        "DCI-NAME": "tempest-results.xml",
        "DCI-MIME": "application/junit",
        "Content-Disposition": "attachment; filename=tempest-results.xml",
        "Content-Type": "application/junit",
    }
    client_admin.post("/api/v1/files", headers=headers, data=content_file)

    query = sql.select([models2.TestsResult])
    tests_results = engine.execute(query).fetchall()
    test_result = dict(tests_results[0])

    assert len(tests_results) == 1
    assert UUID(str(test_result["id"]), version=4)
    assert test_result["name"] == "tempest-results.xml"
    assert test_result["total"] == 131
    assert test_result["skips"] == 13
    assert test_result["failures"] == 1
    assert test_result["errors"] == 0
    assert test_result["success"] == 117
    assert test_result["time"] == 1319


@mock.patch("dci.api.v1.notifications.job_dispatcher")
def test_tests_results_table_with_multiple_testsuites(
    job_dispatcher_mock, engine, client_admin, team1_job_id
):
    with open("tests/data/junit_with_multiple_testsuite.xml", "r") as f:
        content_file = f.read()

    headers = {
        "DCI-JOB-ID": team1_job_id,
        "DCI-NAME": "junit_with_multiple_testsuite.xml",
        "DCI-MIME": "application/junit",
        "Content-Disposition": "attachment; filename=junit_with_multiple_testsuite.xml",
        "Content-Type": "application/junit",
    }
    client_admin.post("/api/v1/files", headers=headers, data=content_file)

    query = sql.select([models2.TestsResult])
    tests_results = engine.execute(query).fetchall()
    test_result = dict(tests_results[0])

    assert len(tests_results) == 1
    assert UUID(str(test_result["id"]), version=4)
    assert test_result["name"] == "junit_with_multiple_testsuite.xml"
    assert test_result["total"] == 6
    assert test_result["skips"] == 1
    assert test_result["failures"] == 1
    assert test_result["errors"] == 1
    assert test_result["success"] == 3
    assert test_result["time"] == 24


@mock.patch("dci.api.v1.notifications.job_dispatcher")
def test_upload_tests_with_invalid_xml(
    mocked_disp, client_admin, hmac_client_team1, rhel_80_topic, rhel_80_component_id
):
    headers = {
        "User-Agent": "python-dciclient",
        "Client-Version": "python-dciclient_0.1.0",
    }

    # 1. schedule two jobs and create their files
    data = {
        "topic_id": rhel_80_topic["id"],
        "components_ids": [rhel_80_component_id],
    }
    job = hmac_client_team1.post(
        "/api/v1/jobs/schedule", headers=headers, data=data
    ).data["job"]

    headers = {
        "DCI-JOB-ID": job["id"],
        "DCI-NAME": "Some Invalid JUnit File",
        "DCI-MIME": "application/junit",
        "Content-Type": "application/junit",
        "Content-Disposition": "attachment; filename=invalid_xml_file.xml",
    }

    file_upload_result = hmac_client_team1.post(
        "/api/v1/files", headers=headers, data="garbage<>!"
    )
    assert file_upload_result.status_code == 400
    assert file_upload_result.data["message"].startswith("Invalid XML: ")
