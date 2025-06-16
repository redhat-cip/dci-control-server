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
import pytest
import uuid


def test_create_remotecis(client_user1, team1_id):
    pr = client_user1.post(
        "/api/v1/remotecis", data={"name": "pname", "team_id": team1_id}
    ).data
    pr_id = pr["remoteci"]["id"]
    gr = client_user1.get("/api/v1/remotecis/%s" % pr_id).data
    assert gr["remoteci"]["name"] == "pname"


def test_create_remotecis_already_exist(client_user1, team1_id):
    pstatus_code = client_user1.post(
        "/api/v1/remotecis", data={"name": "pname", "team_id": team1_id}
    ).status_code
    assert pstatus_code == 201

    pstatus_code = client_user1.post(
        "/api/v1/remotecis", data={"name": "pname", "team_id": team1_id}
    ).status_code
    assert pstatus_code == 409


def test_create_unique_remoteci_against_teams(client_user1, team1_id):
    data = {"name": "foo", "team_id": team1_id}
    res = client_user1.post("/api/v1/remotecis", data=data)
    assert res.status_code == 201

    res = client_user1.post("/api/v1/remotecis", data=data)
    assert res.status_code == 409


def test_get_all_remotecis(client_user1, team1_id):
    remoteci_1 = client_user1.post(
        "/api/v1/remotecis", data={"name": "pname1", "team_id": team1_id}
    ).data
    remoteci_2 = client_user1.post(
        "/api/v1/remotecis", data={"name": "pname2", "team_id": team1_id}
    ).data

    db_all_remotecis = client_user1.get("/api/v1/remotecis?sort=created_at").data
    db_all_remotecis = db_all_remotecis["remotecis"]
    db_all_remotecis_ids = [db_t["id"] for db_t in db_all_remotecis]

    assert db_all_remotecis_ids == [
        remoteci_1["remoteci"]["id"],
        remoteci_2["remoteci"]["id"],
    ]


def test_get_all_remotecis_with_where(client_user1, team1_id):
    pr = client_user1.post(
        "/api/v1/remotecis", data={"name": "pname1", "team_id": team1_id}
    ).data
    pr_id = pr["remoteci"]["id"]

    db_r = client_user1.get("/api/v1/remotecis?where=id:%s" % pr_id).data
    db_r_id = db_r["remotecis"][0]["id"]
    assert db_r_id == pr_id

    db_r = client_user1.get("/api/v1/remotecis?where=name:pname1").data
    db_r_id = db_r["remotecis"][0]["id"]
    assert db_r_id == pr_id


def test_where_invalid(client_admin):
    err = client_admin.get("/api/v1/remotecis?where=id")

    assert err.status_code == 400
    assert err.data["message"] == "Request malformed"
    assert err.data["payload"]["error"] == "where: 'id' is not a 'key value csv'"


def test_get_all_remotecis_with_pagination(client_user1, team1_id):
    # create 4 remotecis and check meta data count
    client_user1.post("/api/v1/remotecis", data={"name": "pname1", "team_id": team1_id})
    client_user1.post("/api/v1/remotecis", data={"name": "pname2", "team_id": team1_id})
    client_user1.post("/api/v1/remotecis", data={"name": "pname3", "team_id": team1_id})
    client_user1.post("/api/v1/remotecis", data={"name": "pname4", "team_id": team1_id})
    remotecis = client_user1.get("/api/v1/remotecis").data
    assert remotecis["_meta"]["count"] == 4

    # verify limit and offset are working well
    remotecis = client_user1.get("/api/v1/remotecis?limit=2&offset=0").data
    assert len(remotecis["remotecis"]) == 2

    remotecis = client_user1.get("/api/v1/remotecis?limit=2&offset=2").data
    assert len(remotecis["remotecis"]) == 2

    # if offset is out of bound, the api returns an empty list
    remotecis = client_user1.get("/api/v1/remotecis?limit=5&offset=300")
    assert remotecis.status_code == 200
    assert remotecis.data["remotecis"] == []


def test_get_all_remotecis_with_sort(client_user1, team1_id):
    # create 2 remotecis ordered by created time
    r_1 = client_user1.post(
        "/api/v1/remotecis", data={"name": "pname1", "team_id": team1_id}
    ).data["remoteci"]
    r_2 = client_user1.post(
        "/api/v1/remotecis", data={"name": "pname2", "team_id": team1_id}
    ).data["remoteci"]

    grs = client_user1.get("/api/v1/remotecis?sort=created_at").data
    grs_ids = [g["id"] for g in grs["remotecis"]]
    assert grs_ids == [r_1["id"], r_2["id"]]

    # test in reverse order
    grs = client_user1.get("/api/v1/remotecis?sort=-created_at").data
    grs_ids = [g["id"] for g in grs["remotecis"]]
    assert grs_ids == [r_2["id"], r_1["id"]]


def test_get_all_remotecis_embed(client_admin, team2_id):
    team = client_admin.get("/api/v1/teams/%s" % team2_id).data["team"]
    # create 2 remotecis
    client_admin.post("/api/v1/remotecis", data={"name": "pname1", "team_id": team2_id})
    client_admin.post("/api/v1/remotecis", data={"name": "pname2", "team_id": team2_id})

    # verify embed
    remotecis = client_admin.get("/api/v1/remotecis?embed=team").data

    for remoteci in remotecis["remotecis"]:
        assert remoteci["team"]["id"] == team["id"]


def test_get_remoteci_by_id(client_user1, team1_id):
    pr = client_user1.post(
        "/api/v1/remotecis", data={"name": "pname", "team_id": team1_id}
    ).data
    pr_id = pr["remoteci"]["id"]

    # get by uuid
    created_r = client_user1.get("/api/v1/remotecis/%s" % pr_id)
    assert created_r.status_code == 200

    created_r = created_r.data
    assert created_r["remoteci"]["id"] == pr_id


def test_get_remoteci_with_embed(client_user1, team1_id):
    team = client_user1.get("/api/v1/teams/%s" % team1_id).data["team"]
    premoteci = client_user1.post(
        "/api/v1/remotecis", data={"name": "pname1", "team_id": team1_id}
    ).data
    r_id = premoteci["remoteci"]["id"]

    # verify embed
    db_remoteci = client_user1.get("/api/v1/remotecis/%s?embed=team" % r_id).data
    assert db_remoteci["remoteci"]["team"]["id"] == team["id"]


def test_get_remoteci_not_found(client_user1):
    result = client_user1.get("/api/v1/remotecis/%s" % uuid.uuid4())
    assert result.status_code == 404


def test_get_remoteci_data(client_user1, team1_id):
    data_data = {"key": "value"}
    data = {"name": "pname1", "team_id": team1_id, "data": data_data}

    premoteci = client_user1.post("/api/v1/remotecis", data=data).data

    r_id = premoteci["remoteci"]["id"]

    r_data = client_user1.get("/api/v1/remotecis/%s/data" % r_id).data
    assert r_data == data_data


def test_get_remoteci_data_specific_keys(client_user1, team1_id):
    data_key = {"key": "value"}
    data_key1 = {"key1": "value1"}

    final_data = {}
    final_data.update(data_key)
    final_data.update(data_key1)
    data = {"name": "pname1", "team_id": team1_id, "data": final_data}

    premoteci = client_user1.post("/api/v1/remotecis", data=data).data

    r_id = premoteci["remoteci"]["id"]

    r_data = client_user1.get("/api/v1/remotecis/%s/data" % r_id).data
    assert r_data == final_data

    r_data = client_user1.get("/api/v1/remotecis/%s/data?keys=key" % r_id).data
    assert r_data == data_key

    r_data = client_user1.get("/api/v1/remotecis/%s/data?keys=key1" % r_id).data
    assert r_data == data_key1

    r_data = client_user1.get("/api/v1/remotecis/%s/data?keys=key,key1" % r_id).data
    assert r_data == final_data


def test_put_remotecis(client_user1, team1_id):
    pr = client_user1.post(
        "/api/v1/remotecis",
        data={"name": "pname", "data": {"a": 1, "b": 2}, "team_id": team1_id},
    )
    assert pr.status_code == 201
    assert pr.data["remoteci"]["public"] is False

    pr_etag = pr.headers.get("ETag")

    gr = client_user1.get("/api/v1/remotecis/%s" % pr.data["remoteci"]["id"])
    assert gr.status_code == 200

    ppr = client_user1.put(
        "/api/v1/remotecis/%s" % gr.data["remoteci"]["id"],
        data={"name": "nname", "public": True, "data": {"c": 3}},
        headers={"If-match": pr_etag},
    )
    assert ppr.status_code == 200
    assert ppr.data["remoteci"]["name"] == "nname"
    assert ppr.data["remoteci"]["public"] is True
    assert set(ppr.data["remoteci"]["data"]) == set(["c"])


def test_delete_remoteci_by_id(client_user1, team1_id):
    pr = client_user1.post(
        "/api/v1/remotecis", data={"name": "pname", "team_id": team1_id}
    )
    pr_etag = pr.headers.get("ETag")
    pr_id = pr.data["remoteci"]["id"]
    assert pr.status_code == 201

    created_r = client_user1.get("/api/v1/remotecis/%s" % pr_id)
    assert created_r.status_code == 200

    deleted_r = client_user1.delete(
        "/api/v1/remotecis/%s" % pr_id, headers={"If-match": pr_etag}
    )
    assert deleted_r.status_code == 204

    gr = client_user1.get("/api/v1/remotecis/%s" % pr_id)
    assert gr.status_code == 404


def test_delete_remoteci_not_found(client_user1):
    result = client_user1.delete(
        "/api/v1/remotecis/%s" % uuid.uuid4(), headers={"If-match": "mdr"}
    )
    assert result.status_code == 404


def test_delete_remoteci_archive_dependencies(
    client_user1,
    team1_remoteci_id,
    rhel_80_topic_id,
    rhel_80_component,
    hmac_client_team1,
):
    data = {
        "topic_id": rhel_80_topic_id,
        "remoteci_id": team1_remoteci_id,
        "components_ids": [rhel_80_component["id"]],
    }
    job = hmac_client_team1.post("/api/v1/jobs/schedule", data=data)
    assert job.status_code == 201

    url = "/api/v1/remotecis/%s" % team1_remoteci_id
    rci = client_user1.get(url)
    etag = rci.data["remoteci"]["etag"]
    assert rci.status_code == 200

    deleted_rci = client_user1.delete(url, headers={"If-match": etag})
    assert deleted_rci.status_code == 204

    url = "/api/v1/jobs/%s" % job.data["job"]["id"]
    job = client_user1.get(url)
    assert job.status_code == 404


# Tests for the isolation


def test_create_remoteci_as_user(client_user1, team1_id, team2_id):
    remoteci = client_user1.post(
        "/api/v1/remotecis", data={"name": "rname", "team_id": team2_id}
    )
    assert remoteci.status_code == 401

    remoteci = client_user1.post(
        "/api/v1/remotecis", data={"name": "rname", "team_id": team1_id}
    )
    assert remoteci.status_code == 201


@pytest.mark.usefixtures("team1_remoteci")
def test_get_all_remotecis_as_user(client_user1, team1_id):
    remotecis = client_user1.get("/api/v1/remotecis")
    assert remotecis.status_code == 200
    assert remotecis.data["_meta"]["count"] == 1
    for remoteci in remotecis.data["remotecis"]:
        assert remoteci["team_id"] == team1_id


def test_get_remoteci_as_user(client_user1, team1_id, team2_remoteci_id):
    remoteci = client_user1.get("/api/v1/remotecis/%s" % team2_remoteci_id)
    assert remoteci.status_code == 401

    remoteci = client_user1.post(
        "/api/v1/remotecis", data={"name": "rname", "team_id": team1_id}
    )
    remoteci = client_user1.get(
        "/api/v1/remotecis/%s" % remoteci.data["remoteci"]["id"]
    )
    assert remoteci.status_code == 200


def test_put_remoteci_as_user(client_user1, team1_id, team2_remoteci_id, client_admin):
    remoteci = client_user1.post(
        "/api/v1/remotecis", data={"name": "rname", "team_id": team1_id}
    )
    remoteci = client_user1.get(
        "/api/v1/remotecis/%s" % remoteci.data["remoteci"]["id"]
    )
    remoteci_etag = remoteci.headers.get("ETag")

    remoteci_put = client_user1.put(
        "/api/v1/remotecis/%s" % remoteci.data["remoteci"]["id"],
        data={"name": "nname"},
        headers={"If-match": remoteci_etag},
    )
    assert remoteci_put.status_code == 200

    remoteci = client_user1.get(
        "/api/v1/remotecis/%s" % remoteci.data["remoteci"]["id"]
    ).data["remoteci"]
    assert remoteci["name"] == "nname"

    remoteci = client_admin.get("/api/v1/remotecis/%s" % team2_remoteci_id)
    remoteci_etag = remoteci.headers.get("ETag")
    remoteci_put = client_user1.put(
        "/api/v1/remotecis/%s" % team2_remoteci_id,
        data={"name": "nname"},
        headers={"If-match": remoteci_etag},
    )
    assert remoteci_put.status_code == 401


def test_delete_remoteci_as_user(
    client_user1, team1_id, client_admin, team2_remoteci_id
):
    remoteci = client_user1.post(
        "/api/v1/remotecis", data={"name": "rname", "team_id": team1_id}
    )
    remoteci = client_user1.get(
        "/api/v1/remotecis/%s" % remoteci.data["remoteci"]["id"]
    )
    remoteci_etag = remoteci.headers.get("ETag")

    remoteci_delete = client_user1.delete(
        "/api/v1/remotecis/%s" % remoteci.data["remoteci"]["id"],
        headers={"If-match": remoteci_etag},
    )
    assert remoteci_delete.status_code == 204

    remoteci = client_admin.get("/api/v1/remotecis/%s" % team2_remoteci_id)
    remoteci_etag = remoteci.headers.get("ETag")
    remoteci_delete = client_user1.delete(
        "/api/v1/remotecis/%s" % team2_remoteci_id, headers={"If-match": remoteci_etag}
    )
    assert remoteci_delete.status_code == 401


def test_change_remoteci_state(client_admin, team2_remoteci_id):
    t = client_admin.get("/api/v1/remotecis/" + team2_remoteci_id).data["remoteci"]
    data = {"state": "inactive"}
    r = client_admin.put(
        "/api/v1/remotecis/" + team2_remoteci_id,
        data=data,
        headers={"If-match": t["etag"]},
    )
    assert r.status_code == 200
    assert r.data["remoteci"]["state"] == "inactive"


def test_change_remoteci_to_invalid_state(client_admin, team2_remoteci_id):
    t = client_admin.get("/api/v1/remotecis/" + team2_remoteci_id).data["remoteci"]
    data = {"state": "kikoolol"}
    r = client_admin.put(
        "/api/v1/remotecis/" + team2_remoteci_id,
        data=data,
        headers={"If-match": t["etag"]},
    )
    assert r.status_code == 400
    current_remoteci = client_admin.get("/api/v1/remotecis/" + team2_remoteci_id)
    assert current_remoteci.status_code == 200
    assert current_remoteci.data["remoteci"]["state"] == "active"


def test_success_attach_user_to_remoteci_in_team_as_admin(
    client_admin, client_user1, user1_id, team1_remoteci_id
):
    r = client_user1.post("/api/v1/remotecis/%s/users" % team1_remoteci_id)

    assert r.status_code == 201


def test_success_attach_po_to_partner_remoteci(
    client_admin, team1_remoteci_id, client_epm
):
    r = client_epm.post("/api/v1/remotecis/%s/users" % team1_remoteci_id)

    assert r.status_code == 201


def test_success_attach_myself_to_remoteci_in_team(
    client_user1, user1_id, team1_remoteci_id
):
    r = client_user1.post("/api/v1/remotecis/%s/users" % team1_remoteci_id)

    assert r.status_code == 201


def test_failure_attach_myself_to_remoteci_not_in_team(
    client_user1, user1_id, team2_remoteci_id
):
    r = client_user1.post("/api/v1/remotecis/%s/users" % team2_remoteci_id)

    assert r.status_code == 401


def test_success_detach_myself_from_remoteci_in_team(
    client_user1, user1_id, team1_remoteci_id
):
    r = client_user1.post("/api/v1/remotecis/%s/users" % team1_remoteci_id)

    assert r.status_code == 201

    r = client_user1.delete(
        "/api/v1/remotecis/%s/users/%s" % (team1_remoteci_id, user1_id)
    )
    assert r.status_code == 204
    u = client_user1.get("/api/v1/users/%s" % user1_id)
    for r in u.data["user"]["remotecis"]:
        assert r["id"] != team1_remoteci_id


def test_get_subscribed_remotecis(team1_remoteci_id, client_user1, user1_id):
    response = client_user1.get("/api/v1/users/%s/remotecis" % user1_id)
    assert response.data["remotecis"] == []
    client_user1.post("/api/v1/remotecis/%s/users" % team1_remoteci_id)
    response = client_user1.get("/api/v1/users/%s/remotecis" % user1_id)
    assert response.data["remotecis"][0]["id"] == team1_remoteci_id


def test_success_ensure_put_api_secret_is_not_leaked(client_user1, team1_id):
    """Test to ensure API secret is not leaked during update."""

    pr = client_user1.post(
        "/api/v1/remotecis",
        data={"name": "pname", "data": {"a": 1, "b": 2}, "team_id": team1_id},
    )
    pr_etag = pr.headers.get("ETag")
    ppr = client_user1.put(
        "/api/v1/remotecis/%s" % pr.data["remoteci"]["id"],
        data={"name": "nname", "public": True, "data": {"c": 3}},
        headers={"If-match": pr_etag},
    )
    assert ppr.status_code == 200
    assert "api_secret" not in ppr.data["remoteci"]
