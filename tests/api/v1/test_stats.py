# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Red Hat, Inc
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
import mock


@mock.patch("dci.api.v1.notifications.dispatcher")
def test_get_stats(n, admin, job_admin, user, job_user, topic_user_id, product):
    admin.post(
        "/api/v1/jobstates", data={"job_id": job_admin["id"], "status": "failure"}
    )
    user.post("/api/v1/jobstates", data={"job_id": job_user["id"], "status": "success"})
    assert admin.get("/api/v1/stats").data["stats"] == [
        {
            "product": {"id": product["id"], "name": product["name"]},
            "percentageOfSuccess": 50,
            "jobs": [
                {
                    "id": job_admin["id"],
                    "remoteci_name": "admin remoteci",
                    "created_at": job_admin["created_at"],
                    "status": "failure",
                    "team_name": "admin",
                },
                {
                    "id": job_user["id"],
                    "remoteci_name": "user remoteci",
                    "created_at": job_user["created_at"],
                    "status": "success",
                    "team_name": "user",
                },
            ],
            "topic": {"id": topic_user_id, "name": "topic_user_name"},
        }
    ]
    assert user.get("/api/v1/stats").data["stats"] == [
        {
            "product": {"id": product["id"], "name": product["name"]},
            "percentageOfSuccess": 100,
            "jobs": [
                {
                    "id": job_user["id"],
                    "remoteci_name": "user remoteci",
                    "created_at": job_user["created_at"],
                    "status": "success",
                    "team_name": "user",
                }
            ],
            "topic": {"id": topic_user_id, "name": "topic_user_name"},
        }
    ]
