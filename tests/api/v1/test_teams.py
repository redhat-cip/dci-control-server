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
import uuid


def test_create_teams(client_admin, team_admin_id):
    pt = client_admin.post("/api/v1/teams", data={"name": "pname"}).data
    pt_id = pt["team"]["id"]
    gt = client_admin.get("/api/v1/teams/%s" % pt_id).data
    assert gt["team"]["name"] == "pname"

    pt = client_admin.post("/api/v1/teams", data={"name": "pname2"}).data
    pt_id = pt["team"]["id"]
    gt = client_admin.get("/api/v1/teams/%s" % pt_id).data
    assert gt["team"]["name"] == "pname2"


def test_create_teams_already_exist(client_admin):
    pstatus_code = client_admin.post(
        "/api/v1/teams", data={"name": "pname"}
    ).status_code
    assert pstatus_code == 201

    pstatus_code = client_admin.post(
        "/api/v1/teams", data={"name": "pname"}
    ).status_code
    assert pstatus_code == 409


def test_get_all_teams(client_admin):
    # TODO(yassine): Currently there is already 3 teams created in the DB,
    # this will be fixed later.
    db_teams = client_admin.get("/api/v1/teams?sort=created_at").data
    db_teams = db_teams["teams"]
    db_teams_ids = [db_t["id"] for db_t in db_teams]

    test_1 = client_admin.post("/api/v1/teams", data={"name": "pname1"}).data
    test_2 = client_admin.post("/api/v1/teams", data={"name": "pname2"}).data
    db_teams_ids.extend([test_1["team"]["id"], test_2["team"]["id"]])

    db_get_all_teams = client_admin.get("/api/v1/teams?sort=created_at").data
    db_get_all_teams = db_get_all_teams["teams"]
    db_get_all_teams_ids = [db_t["id"] for db_t in db_get_all_teams]

    assert db_get_all_teams_ids == db_teams_ids


def test_get_all_teams_with_where(client_admin):
    pt = client_admin.post("/api/v1/teams", data={"name": "pname1"}).data
    pt_id = pt["team"]["id"]

    db_t = client_admin.get("/api/v1/teams?where=id:%s" % pt_id).data
    db_t_id = db_t["teams"][0]["id"]
    assert db_t_id == pt_id

    db_t = client_admin.get("/api/v1/teams?where=name:pname1").data
    db_t_id = db_t["teams"][0]["id"]
    assert db_t_id == pt_id


def test_where_invalid(client_admin):
    err = client_admin.get("/api/v1/teams?where=id")

    assert err.status_code == 400
    assert err.data["message"] == "Request malformed"
    assert err.data["payload"]["error"] == "where: 'id' is not a 'key value csv'"


def test_get_all_teams_with_pagination(client_admin):
    ts = client_admin.get("/api/v1/teams").data
    current_teams = ts["_meta"]["count"]
    # create 4 components types and check meta data count
    client_admin.post("/api/v1/teams", data={"name": "pname1"})
    client_admin.post("/api/v1/teams", data={"name": "pname2"})
    client_admin.post("/api/v1/teams", data={"name": "pname3"})
    client_admin.post("/api/v1/teams", data={"name": "pname4"})
    ts = client_admin.get("/api/v1/teams").data
    assert ts["_meta"]["count"] == current_teams + 4

    # verify limit and offset are working well
    ts = client_admin.get("/api/v1/teams?limit=2&offset=0").data
    assert len(ts["teams"]) == 2

    ts = client_admin.get("/api/v1/teams?limit=2&offset=2").data
    assert len(ts["teams"]) == 2

    # if offset is out of bound, the api returns an empty list
    ts = client_admin.get("/api/v1/teams?limit=5&offset=300")
    assert ts.status_code == 200
    assert ts.data["teams"] == []


def test_get_all_teams_with_sort(client_admin):
    # TODO(yassine): Currently there is already 3 teams created in the DB,
    # this will be fixed later.
    _db_teams = client_admin.get("/api/v1/teams?sort=created_at").data
    db_teams = [dbt["id"] for dbt in _db_teams["teams"]]

    # create 2 teams ordered by created time
    t_1 = client_admin.post("/api/v1/teams", data={"name": "pname1"}).data["team"]
    t_2 = client_admin.post("/api/v1/teams", data={"name": "pname2"}).data["team"]

    _gts = client_admin.get("/api/v1/teams?sort=created_at").data
    db_teams.extend([t_1["id"], t_2["id"]])
    gts = [gt["id"] for gt in _gts["teams"]]
    assert gts == db_teams

    # test in reverse order
    db_teams.reverse()
    gts = client_admin.get("/api/v1/teams?sort=-created_at").data
    gts = [g["id"] for g in gts["teams"]]
    assert gts == db_teams


def test_get_team_by_id(client_admin):
    pt = client_admin.post("/api/v1/teams", data={"name": "pname"}).data
    pt_id = pt["team"]["id"]

    # get by uuid
    created_t = client_admin.get("/api/v1/teams/%s" % pt_id)
    assert created_t.status_code == 200

    created_t = created_t.data
    assert created_t["team"]["id"] == pt_id


def test_get_team_not_found(client_admin):
    result = client_admin.get("/api/v1/teams/%s" % uuid.uuid4())
    assert result.status_code == 404


def test_put_teams(client_admin):
    pt = client_admin.post("/api/v1/teams", data={"name": "pname"})
    assert pt.status_code == 201

    pt_etag = pt.headers.get("ETag")

    gt = client_admin.get("/api/v1/teams/%s" % pt.data["team"]["id"])
    assert gt.status_code == 200

    ppt = client_admin.put(
        "/api/v1/teams/%s" % gt.data["team"]["id"],
        data={"name": "nname"},
        headers={"If-match": pt_etag},
    )
    assert ppt.status_code == 200
    assert ppt.data["team"]["name"] == "nname"


def test_put_team_external_flag(client_user1, client_admin, client_epm):
    cteam = client_admin.post("/api/v1/teams", data={"name": "pname"})
    cteam_id = cteam.data["team"]["id"]

    cteam = client_epm.get("/api/v1/teams/%s" % cteam_id)
    assert cteam.status_code == 200
    cteam_etag = cteam.headers.get("ETag")

    cteam_put = client_user1.put(
        "/api/v1/teams/%s" % cteam_id,
        data={"external": False},
        headers={"If-match": cteam_etag},
    )
    assert cteam_put.status_code == 401

    cteam_put = client_admin.put(
        "/api/v1/teams/%s" % cteam_id,
        data={"external": False},
        headers={"If-match": cteam_etag},
    )
    assert cteam_put.status_code == 200
    assert cteam_put.data["team"]["external"] is False


def test_delete_team_by_id(client_admin):
    pt = client_admin.post("/api/v1/teams", data={"name": "pname"})
    pt_etag = pt.headers.get("ETag")
    pt_id = pt.data["team"]["id"]
    assert pt.status_code == 201

    created_t = client_admin.get("/api/v1/teams/%s" % pt_id)
    assert created_t.status_code == 200

    deleted_t = client_admin.delete(
        "/api/v1/teams/%s" % pt_id, headers={"If-match": pt_etag}
    )
    assert deleted_t.status_code == 204

    gt = client_admin.get("/api/v1/teams/%s" % pt_id)
    assert gt.status_code == 404


def test_delete_team_not_found(client_admin):
    result = client_admin.delete(
        "/api/v1/teams/%s" % uuid.uuid4(), headers={"If-match": "mdr"}
    )
    assert result.status_code == 404


def test_delete_team_archive_dependencies(
    client_admin, hmac_client_team1, rhel_product, team1, rhel_80_topic_id
):
    user = client_admin.post(
        "/api/v1/users",
        data={
            "name": "pname",
            "password": "ppass",
            "fullname": "P Name",
            "email": "pname@example.org",
        },
    )
    assert user.status_code == 201

    remoteci = client_admin.post(
        "/api/v1/remotecis", data={"name": "pname", "team_id": team1["id"]}
    )
    remoteci_id = remoteci.data["remoteci"]["id"]
    assert remoteci.status_code == 201

    topic = client_admin.post(
        "/api/v1/topics",
        data={
            "name": "topic_name",
            "product_id": rhel_product["id"],
            "component_types": ["type1", "type2"],
        },
    )
    topic_id = topic.data["topic"]["id"]
    assert topic.status_code == 201

    data = {
        "name": "pname",
        "type": "gerrit_review",
        "url": "http://example.com/",
        "topic_id": topic_id,
        "state": "active",
    }
    component = client_admin.post("/api/v1/components", data=data)
    component_id = component.data["component"]["id"]
    assert component.status_code == 201

    data = {
        "team_id": team1["id"],
        "comment": "kikoolol",
        "components": [component_id],
        "topic_id": rhel_80_topic_id,
    }
    job = hmac_client_team1.post("/api/v1/jobs", data=data)
    job_id = job.data["job"]["id"]
    assert job.status_code == 201

    deleted_team = client_admin.delete(
        "/api/v1/teams/%s" % team1["id"], headers={"If-match": team1["etag"]}
    )
    assert deleted_team.status_code == 204

    deleted_remoteci = client_admin.get("/api/v1/remotecis/%s" % remoteci_id)
    assert deleted_remoteci.status_code == 404

    deleted_job = client_admin.get("/api/v1/jobs/%s" % job_id)
    assert deleted_job.status_code == 404


def test_deleted_team_has_no_users(client_admin, user1_id, team1_id):
    pt = client_admin.post("/api/v1/teams", data={"name": "pname"})
    pt_etag = pt.headers.get("ETag")
    pt_id = pt.data["team"]["id"]
    assert pt.status_code == 201

    created_t = client_admin.get("/api/v1/teams/%s" % pt_id)
    assert created_t.status_code == 200

    pu = client_admin.post("/api/v1/teams/%s/users/%s" % (pt_id, user1_id), data={})
    assert pu.status_code == 201

    uteams = client_admin.get("/api/v1/users/%s/teams" % user1_id)
    assert uteams.status_code == 200
    assert len(uteams.data["teams"]) == 2
    team_ids = {t["id"] for t in uteams.data["teams"]}
    assert team_ids == set([pt_id, team1_id])

    deleted_t = client_admin.delete(
        "/api/v1/teams/%s" % pt_id, headers={"If-match": pt_etag}
    )
    assert deleted_t.status_code == 204

    uteams = client_admin.get("/api/v1/users/%s/teams" % user1_id)
    assert uteams.status_code == 200
    assert len(uteams.data["teams"]) == 1
    team_ids = {t["id"] for t in uteams.data["teams"]}
    assert team_ids == set(
        [
            team1_id,
        ]
    )


# Tests for the isolation


def test_create_team_as_user(client_user1):
    team = client_user1.post("/api/v1/teams", data={"name": "pname"})
    assert team.status_code == 401


def test_get_all_teams_as_user(client_user1):
    teams = client_user1.get("/api/v1/teams")
    assert teams.status_code == 200


def test_get_teams_as_user(client_user1, team1_id, team_admin_id):
    team = client_user1.get("/api/v1/teams/%s" % team_admin_id)
    assert team.status_code == 401

    team = client_user1.get("/api/v1/teams/%s" % team1_id)
    assert team.status_code == 200

    teams = client_user1.get("/api/v1/teams")
    assert teams.status_code == 200
    assert len(teams.data["teams"]) == 1


def test_change_team_state(client_admin, team2_id):
    t = client_admin.get("/api/v1/teams/" + team2_id).data["team"]
    data = {"state": "inactive"}
    r = client_admin.put(
        "/api/v1/teams/" + team2_id, data=data, headers={"If-match": t["etag"]}
    )
    assert r.status_code == 200
    assert r.data["team"]["state"] == "inactive"


def test_change_team_to_invalid_state(client_admin, team2_id):
    t = client_admin.get("/api/v1/teams/" + team2_id).data["team"]
    data = {"state": "kikoolol"}
    r = client_admin.put(
        "/api/v1/teams/" + team2_id, data=data, headers={"If-match": t["etag"]}
    )
    assert r.status_code == 400
    current_team = client_admin.get("/api/v1/teams/" + team2_id)
    assert current_team.status_code == 200
    assert current_team.data["team"]["state"] == "active"


# Only super admin can delete a team
def test_delete_as_admin(client_user1, team1_id, client_admin):
    team = client_user1.get("/api/v1/teams/%s" % team1_id)
    team_etag = team.headers.get("ETag")

    team_delete = client_user1.delete(
        "/api/v1/teams/%s" % team1_id, headers={"If-match": team_etag}
    )
    assert team_delete.status_code == 401

    team_delete = client_admin.delete(
        "/api/v1/teams/%s" % team1_id, headers={"If-match": team_etag}
    )
    assert team_delete.status_code == 204


def test_success_update_field_by_field(client_admin, team1_id):
    t = client_admin.get("/api/v1/teams/%s" % team1_id).data["team"]

    client_admin.put(
        "/api/v1/teams/%s" % team1_id,
        data={"state": "inactive"},
        headers={"If-match": t["etag"]},
    )

    t = client_admin.get("/api/v1/teams/%s" % team1_id).data["team"]

    assert t["name"] == "team1"
    assert t["state"] == "inactive"
    assert t["country"] is None

    client_admin.put(
        "/api/v1/teams/%s" % team1_id,
        data={"country": "FR"},
        headers={"If-match": t["etag"]},
    )

    t = client_admin.get("/api/v1/teams/%s" % team1_id).data["team"]

    assert t["name"] == "team1"
    assert t["state"] == "inactive"
    assert t["country"] == "FR"


def test_epm_should_be_able_to_create_and_edit_a_team(client_epm):
    r = client_epm.post("/api/v1/teams", data={"name": "t1"})
    assert r.status_code == 201
    r = client_epm.put(
        "/api/v1/teams/%s" % r.data["team"]["id"],
        data={"name": "t1 updated"},
        headers={"If-match": r.headers.get("ETag")},
    )
    assert r.status_code == 200


def test_get_all_teams_allowed_for_rh_employee(client_epm, client_rh_employee):
    nb_teams = client_rh_employee.get("/api/v1/teams").data["_meta"]["count"]
    r = client_epm.post("/api/v1/teams", data={"name": "rh employee can see me"})
    assert r.status_code == 201
    teams = client_rh_employee.get("/api/v1/teams?sort=-created_at").data["teams"]
    assert teams[0]["name"] == "rh employee can see me"
    assert len(teams) == nb_teams + 1


def test_nrt_update_team_after_get(client_admin, team2_id):
    team = client_admin.get("/api/v1/teams/%s" % team2_id).data["team"]
    new_team_name = "new team name"
    assert team["name"] != new_team_name
    team["name"] = new_team_name
    r = client_admin.put(
        "/api/v1/teams/%s" % team2_id,
        data=team,
        headers={"If-match": team["etag"]},
    )
    assert r.status_code == 200
    team = client_admin.get("/api/v1/teams/%s" % team2_id).data["team"]
    assert team["name"] == "new team name"


def test_create_and_update_team_with_has_pre_release_access_flag(
    client_admin, client_epm
):
    team_data = {"name": "new team", "external": True, "has_pre_release_access": False}
    create_team_request = client_admin.post("/api/v1/teams", data=team_data)
    assert create_team_request.status_code == 201

    team_created = create_team_request.data["team"]
    assert team_created["has_pre_release_access"] is False

    update_team_request = client_epm.put(
        "/api/v1/teams/%s" % team_created["id"],
        data={"has_pre_release_access": True},
        headers={"If-match": team_created["etag"]},
    )
    assert update_team_request.status_code == 200

    team_updated = update_team_request.data["team"]
    assert team_updated["has_pre_release_access"]


def test_get_products_team_has_access_to(client_admin, team1_id, team2_id):
    products_team_user_request = client_admin.get(
        "/api/v1/teams/%s/products" % team1_id
    )
    assert products_team_user_request.status_code == 200
    products = products_team_user_request.data["products"]
    assert sorted([p["name"] for p in products]) == ["OpenStack", "RHEL"]

    products_team_user2_request = client_admin.get(
        "/api/v1/teams/%s/products" % team2_id
    )
    assert products_team_user2_request.status_code == 200
    products = products_team_user2_request.data["products"]
    assert sorted([p["name"] for p in products]) == ["RHEL"]
