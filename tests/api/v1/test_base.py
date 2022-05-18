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


def test_where_name_case_insensitive(user, team_user_id):
    remoteci = user.post(
        "/api/v1/remotecis", data={"name": "My remoteci", "team_id": team_user_id}
    ).data["remoteci"]
    remoteci_id = remoteci["id"]

    remotecis = user.get("/api/v1/remotecis?where=id:%s" % remoteci_id).data[
        "remotecis"
    ]
    assert len(remotecis) == 1
    assert remotecis[0]["id"] == remoteci_id

    remotecis = user.get("/api/v1/remotecis?where=name:My%20remote*").data["remotecis"]
    assert len(remotecis) == 1
    assert remotecis[0]["id"] == remoteci_id

    remotecis = user.get("/api/v1/remotecis?where=name:my%20remote*").data["remotecis"]
    assert len(remotecis) == 1
    assert remotecis[0]["id"] == remoteci_id

    remotecis = user.get("/api/v1/remotecis?where=name:My%20remoteci").data["remotecis"]
    assert len(remotecis) == 1
    assert remotecis[0]["id"] == remoteci_id

    remotecis = user.get("/api/v1/remotecis?where=name:mY%20RemOteCi").data["remotecis"]
    assert len(remotecis) == 1
    assert remotecis[0]["id"] == remoteci_id


def test_where_with_different_column_types(user):
    request = user.get("/api/v1/jobs?where=name:foo")
    assert request.status_code == 200

    request = user.get("/api/v1/jobs?where=id:d781d517-643d-4a35-af35-4702a12db9ae")
    assert request.status_code == 200

    request = user.get(
        "/api/v1/jobs?where=remoteci_id:d781d517-643d-4a35-af35-4702a12db9ae"
    )
    assert request.status_code == 200

    request = user.get("/api/v1/jobs?where=duration:134")
    assert request.status_code == 200

    request = user.get("/api/v1/jobs?where=tags:134")
    assert request.status_code == 200

    request = user.get("/api/v1/jobs?where=state:active")
    assert request.status_code == 200


def test_where_with_forbidden_column_names(user):
    request = user.get("/api/v1/jobs?where=data:eyJhdXRoIjogInNlY3JldCJ9")
    assert request.status_code == 400

    request = user.get(
        "/api/v1/jobs?where=api_secret:UKRulywqaiXUdBHeKAZYvzUlZbgPw5BswOOIaWmu1ZthjIrvDOyQ7kLsmkHAtPYb"
    )
    assert request.status_code == 400

    request = user.get(
        "/api/v1/jobs?where=password:5BswOOIaWmu1ZthjIrvDOyQ7kLsmkHAtPYbUKRulywqaiXUdBHeKAZYvzUlZbgPw"
    )
    assert request.status_code == 400

    request = user.get("/api/v1/jobs?where=cert_fp:brute_force")
    assert request.status_code == 400
