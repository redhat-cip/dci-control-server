# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Red Hat, Inc
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


def test_job_upgrade(
    client_admin,
    team1_job_id,
    team2_remoteci_id,
    rhel_80_topic_id,
    rhel_80_component,
):
    job_upgraded = client_admin.post(
        "/api/v1/jobs/upgrade", data={"job_id": team1_job_id}
    )
    # the topic 'topic_id' does not contains a 'next_topic_id' field
    assert job_upgraded.status_code == 400

    # adds a next topic to 'topic_user_id'
    topic = client_admin.get("/api/v1/topics/%s" % rhel_80_topic_id)
    topic_user_etag = topic.data["topic"]["etag"]

    assert (
        client_admin.put(
            "/api/v1/topics/%s" % rhel_80_topic_id,
            data={"next_topic_id": rhel_80_topic_id},
            headers={"If-match": topic_user_etag},
        ).status_code
        == 200
    )

    # request for the upgrade of the first job
    job_upgraded = client_admin.post(
        "/api/v1/jobs/upgrade", data={"job_id": team1_job_id}
    )

    assert job_upgraded.status_code == 201
    assert job_upgraded.data["job"]["previous_job_id"] == team1_job_id
    # job_upgraded is a job against the next version of topic
