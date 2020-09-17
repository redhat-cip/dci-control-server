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


def test_create_get_analytics(admin, job_user_id):
    analytics = admin.get("/api/v1/jobs/%s/analytics" % job_user_id)
    assert analytics.data["analytics"] == []
    anc = admin.post(
        "/api/v1/jobs/%s/analytics" % job_user_id,
        data={
            "name": "rhsm pool issue",
            "type": "infrastructure",
            "url": "http://bugzilla/1",
            "data": {"root_cause": "pool not found"},
        },
    )
    assert anc.status_code == 201
    anc_id = anc.data["analytic"]["id"]
    analytic = admin.get("/api/v1/jobs/%s/analytics/%s" % (job_user_id, anc_id))
    analytic = analytic.data["analytic"]

    assert analytic["name"] == "rhsm pool issue"
    assert analytic["type"] == "infrastructure"
    assert analytic["url"] == "http://bugzilla/1"
    assert analytic["data"] == {"root_cause": "pool not found"}


def test_get_several_analytics(admin, job_user_id):
    # get with embeds
    analytics = admin.get("/api/v1/jobs/%s?embed=analytics" % job_user_id)
    assert len(analytics.data["job"]["analytics"]) == 0

    for i in range(3):
        job = admin.post(
            "/api/v1/jobs/%s/analytics" % job_user_id,
            data={
                "name": "rhsm pool issue %s" % i,
                "type": "infrastructure",
                "url": "http://bugzilla/%s" % i,
                "data": {"root_cause": "pool not found"},
            },
        )
        assert job.status_code == 201

    analytics = admin.get("/api/v1/jobs/%s/analytics" % job_user_id)
    assert len(analytics.data["analytics"]) == 3
    # get with embeds
    analytics = admin.get("/api/v1/jobs/%s?embed=analytics" % job_user_id)
    assert len(analytics.data["job"]["analytics"]) == 3


def test_put_analytic(admin, job_user_id):
    anc = admin.post(
        "/api/v1/jobs/%s/analytics" % job_user_id,
        data={
            "name": "rhsm pool issue",
            "type": "infrastructure",
            "url": "http://bugzilla/1",
            "data": {"root_cause": "pool not found"},
        },
    )
    anc_id = anc.data["analytic"]["id"]
    anc_etag = anc.data["analytic"]["etag"]
    res = admin.put(
        "/api/v1/jobs/%s/analytics/%s" % (job_user_id, anc_id),
        headers={"If-match": anc_etag},
        data={
            "type": "product",
            "url": "http://bugzilla/2",
            "data": {"root_cause": "no pool"},
        },
    )
    assert res.status_code == 200
    analytics = admin.get("/api/v1/jobs/%s/analytics" % job_user_id)
    assert analytics.data["analytics"][0]["type"] == "product"


def test_delete_analytics(admin, job_user_id):
    anc = admin.post(
        "/api/v1/jobs/%s/analytics" % job_user_id,
        data={
            "name": "rhsm pool issue",
            "type": "infrastructure",
            "url": "http://bugzilla/1",
            "data": {"root_cause": "pool not found"},
        },
    )
    anc_id = anc.data["analytic"]["id"]
    assert anc.status_code == 201
    analytics = admin.get("/api/v1/jobs/%s/analytics" % job_user_id)
    assert len(analytics.data["analytics"]) == 1
    admin.delete("/api/v1/jobs/%s/analytics/%s" % (job_user_id, anc_id))
    analytics = admin.get("/api/v1/jobs/%s/analytics" % job_user_id)
    assert len(analytics.data["analytics"]) == 0
