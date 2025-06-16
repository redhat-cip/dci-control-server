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


def test_get_identity_admin(client_admin, team_admin_id):
    response = client_admin.get("/api/v1/identity")
    assert response.status_code == 200
    assert "identity" in response.data
    identity = response.data["identity"]
    assert team_admin_id in identity["teams"]
    assert identity["teams"][team_admin_id]["name"] == "admin"
    assert identity["teams"][team_admin_id]["id"] == team_admin_id


def test_get_identity_unauthorized(client_unauthorized):
    response = client_unauthorized.get("/api/v1/identity")
    assert response.status_code == 401


def test_get_identity_user(client_user1, team1_id):
    response = client_user1.get("/api/v1/identity")
    assert response.status_code == 200
    assert "identity" in response.data
    identity = response.data["identity"]
    assert identity["name"] == "user1"
    assert identity["teams"][team1_id]["name"] == "team1"
    assert identity["teams"][team1_id]["id"] == team1_id


def get_user(flask_user, name):
    get = flask_user.get("/api/v1/users?where=name:%s" % name)
    get2 = flask_user.get("/api/v1/users/%s" % get.data["users"][0]["id"])
    return get2.data["user"], get2.headers.get("ETag")


def test_update_identity_password(client_admin, client_user1):
    user_data, user_etag = get_user(client_admin, "user1")

    assert client_user1.get("/api/v1/identity").status_code == 200

    assert (
        client_user1.put(
            "/api/v1/identity",
            data={"current_password": "user1", "new_password": "password"},
            headers={"If-match": user_etag},
        ).status_code
        == 200
    )

    assert client_user1.get("/api/v1/identity").status_code == 401

    user_data, user_etag = get_user(client_admin, "user1")

    assert (
        client_admin.put(
            "/api/v1/users/%s" % user_data["id"],
            data={"password": "user1"},
            headers={"If-match": user_etag},
        ).status_code
        == 200
    )

    assert client_user1.get("/api/v1/identity").status_code == 200


def test_update_current_user_current_password_wrong(client_admin, client_user1):
    user_data, user_etag = get_user(client_admin, "user1")

    assert client_user1.get("/api/v1/identity").status_code == 200

    assert (
        client_user1.put(
            "/api/v1/identity",
            data={"current_password": "wrong_password", "new_password": ""},
            headers={"If-match": user_etag},
        ).status_code
        == 400
    )

    assert client_user1.get("/api/v1/identity").status_code == 200


def test_update_current_user_new_password_empty(client_admin, client_user1):
    user_data, user_etag = get_user(client_admin, "user1")

    assert client_user1.get("/api/v1/identity").status_code == 200

    assert (
        client_user1.put(
            "/api/v1/identity",
            data={"current_password": "user1", "new_password": ""},
            headers={"If-match": user_etag},
        ).status_code
        == 200
    )

    assert client_user1.get("/api/v1/identity").status_code == 200


def test_update_current_user(client_admin, client_user1):
    user_data, user_etag = get_user(client_admin, "user1")

    assert client_user1.get("/api/v1/identity").status_code == 200

    me = client_user1.put(
        "/api/v1/identity",
        data={
            "current_password": "user1",
            "new_password": "",
            "email": "new_email@example.org",
            "fullname": "New Name",
            "timezone": "Europe/Paris",
        },
        headers={"If-match": user_etag},
    )
    assert me.status_code == 200
    assert me.data["user"]["email"] == "new_email@example.org"
    assert me.data["user"]["fullname"] == "New Name"
    assert me.data["user"]["timezone"] == "Europe/Paris"


def test_update_current_user_sso(client_rh_employee, app, client_admin):
    assert client_rh_employee.get("/api/v1/identity").status_code == 200
    user_data, user_etag = get_user(client_admin, "rh_employee")
    me = client_rh_employee.put(
        "/api/v1/identity",
        data={
            "email": "new_email@example.org",
            "fullname": "New Name",
            "timezone": "Europe/Paris",
        },
        headers={"If-match": user_etag},
    )
    assert me.status_code == 200
    assert me.data["user"]["email"] == "new_email@example.org"
    assert me.data["user"]["fullname"] == "New Name"
    assert me.data["user"]["timezone"] == "Europe/Paris"
