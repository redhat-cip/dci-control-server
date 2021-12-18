# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2017 Red Hat, Inc
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


def test_purge_resource(admin, product):
    data = {
        "name": "tname",
        "product_id": product["id"],
        "component_types": ["type1", "type2"],
    }
    pt = admin.post("/api/v1/topics", data=data)
    pt_id = pt.data["topic"]["id"]
    assert pt.status_code == 201

    ppt = admin.delete(
        "/api/v1/topics/%s" % pt_id, headers={"If-match": pt.data["topic"]["etag"]}
    )
    assert ppt.status_code == 204

    to_purge = admin.get("/api/v1/topics/purge").data
    assert len(to_purge["topics"]) == 1

    to_purge = admin.post("/api/v1/topics/purge")
    assert to_purge.status_code == 204

    to_purge = admin.get("/api/v1/topics/purge").data
    assert len(to_purge["topics"]) == 0


def test_purge_resource_ORM(admin, team_admin_id):
    feeder = admin.post(
        "/api/v1/feeders", data={"name": "feeder", "team_id": team_admin_id}
    ).data["feeder"]
    admin.delete(
        "/api/v1/feeders/%s" % feeder["id"],
        headers={"If-match": feeder["etag"]},
    )

    feeders_to_purge = admin.get("/api/v1/feeders/purge").data["feeders"]
    assert len(feeders_to_purge) == 1
    assert feeders_to_purge[0]["id"] == feeder["id"]

    purge = admin.post("/api/v1/feeders/purge")
    assert purge.status_code == 204

    feeders_to_purge = admin.get("/api/v1/feeders/purge").data["feeders"]
    assert len(feeders_to_purge) == 0
