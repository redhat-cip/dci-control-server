# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Red Hat, Inc
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

import collections
import six
import uuid

import mock

from dci.common import utils
from dci.stores.s3 import S3
import tests.utils as t_utils

AWSS3 = "dci.stores.s3.S3"
FileDesc = collections.namedtuple("FileDesc", ["name", "content"])


# COMPONENTS
def test_components(client_admin, client_rh_employee, app, rhel_80_topic_id):
    pc = client_admin.post(
        "/api/v1/components",
        data={
            "name": "pname%s" % uuid.uuid4(),
            "type": "gerrit_review",
            "topic_id": rhel_80_topic_id,
        },
    ).data
    pc_id = pc["component"]["id"]
    # get all components of a topic
    cmpts = client_rh_employee.get("/api/v1/topics/%s/components" % rhel_80_topic_id)
    assert cmpts.status_code == 200
    # get specific component
    cmpt = client_rh_employee.get("/api/v1/components/%s" % pc_id)
    assert cmpt.status_code == 200
    # get component's files

    with mock.patch(AWSS3, spec=S3) as mock_s3:
        mockito = mock.MagicMock()

        mockito.get.return_value = ["test", six.StringIO("lollollel")]
        head_result = {
            "etag": utils.gen_etag(),
            "content-type": "stream",
            "content-length": 3,
        }
        mockito.head.return_value = head_result

        mock_s3.return_value = mockito

        url = "/api/v1/components/%s/files" % pc_id
        files = client_rh_employee.get(url)
        # get components files
        assert files.status_code == 200
        c_file = client_admin.post(url, data="lol").data["component_file"]

        url = "/api/v1/components/%s/files/%s/content" % (pc_id, c_file["id"])
        # get component's file content
        d_file = client_rh_employee.get(url)
        assert d_file.status_code == 200


# FILES
def test_files(client_admin, client_rh_employee, team1_job_id):
    files = client_rh_employee.get("/api/v1/jobs/%s/files" % team1_job_id)
    assert files.status_code == 200
    # get file content
    with mock.patch(AWSS3, spec=S3) as mock_s3:
        mockito = mock.MagicMock()

        head_result = {
            "etag": utils.gen_etag(),
            "content-type": "stream",
            "content-length": 7,
        }

        mockito.head.return_value = head_result
        mockito.get.return_value = [head_result, six.StringIO("azertyuiop1234567890")]
        mock_s3.return_value = mockito
        content = "azertyuiop1234567890"
        file = t_utils.create_file(client_admin, team1_job_id, "foo", content)

        get_file = client_rh_employee.get("/api/v1/files/%s" % file["id"])

        assert get_file.status_code == 200


# JOBS
def test_jobs(
    client_rh_employee, app, hmac_client_team1, rhel_80_topic_id, rhel_80_component
):
    data = {"components_ids": [rhel_80_component["id"]], "topic_id": rhel_80_topic_id}
    job_1 = hmac_client_team1.post("/api/v1/jobs/schedule", data=data)
    # get all jobs
    db_all_jobs = client_rh_employee.get("/api/v1/jobs?sort=created_at").data
    assert len(db_all_jobs["jobs"]) > 0
    # get specific job
    job_id = job_1.data["job"]["id"]
    job = client_rh_employee.get("/api/v1/jobs/%s" % job_id)
    assert job.status_code == 200

    # get job result
    job_result = client_rh_employee.get("/api/v1/jobs/%s/results" % job_id)
    assert job_result.status_code == 200


def test_nrt_red_hat_remoteci_can_see_all_jobs(hmac_client_redhat, team1_job):
    jobs = hmac_client_redhat.get("/api/v1/jobs?sort=created_at").data["jobs"]
    assert [job["id"] for job in jobs] == [team1_job["id"]]


# JOBSTATES
def test_jobstates(client_rh_employee, team1_job_id, app):
    jobstates = client_rh_employee.get("/api/v1/jobs/%s/jobstates" % team1_job_id)
    assert jobstates.status_code == 200


# PRODUCTS
def test_products(client_rh_employee, app):
    products = client_rh_employee.get("/api/v1/products")
    assert products.status_code == 200


# TOPICS
def test_topics(client_rh_employee, app, rhel_80_topic_id):
    gtopic = client_rh_employee.get("/api/v1/topics/%s" % rhel_80_topic_id)
    assert gtopic.status_code == 200
    gtopics = client_rh_employee.get("/api/v1/topics")
    assert gtopics.status_code == 200
