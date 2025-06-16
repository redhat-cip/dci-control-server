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

from __future__ import unicode_literals


def test_success_create_feeder_authorized_users(client_admin, client_epm, team1_id):
    """Test to ensure user with proper permissions can create feeders

    Currently only the SUPER_ADMIN and EPM have such
    a permission.
    """

    feeder_from_admin = {"name": "feeder-from-admin", "team_id": team1_id}
    feeder_from_epm = {"name": "feeder-from-po", "team_id": team1_id}

    admin_result = client_admin.post("/api/v1/feeders", data=feeder_from_admin)
    epm_result = client_epm.post("/api/v1/feeders", data=feeder_from_epm)

    assert admin_result.status_code == 201
    assert admin_result.data["feeder"]["name"] == feeder_from_admin["name"]

    assert epm_result.status_code == 201
    assert epm_result.data["feeder"]["name"] == feeder_from_epm["name"]


def test_failure_create_feeder_unauthorized_users(client_user1, team1_id):
    """Test to ensure user w/o proper permissions can't create feeders

    Currently only the SUPER_ADMIN and EPM have such
    a permission. So we test with a regular USER.
    """

    feeder_from_user = {"name": "feeder-from-user", "team_id": team1_id}

    user_result = client_user1.post("/api/v1/feeders", data=feeder_from_user)

    assert user_result.status_code == 401


def test_success_get_feeder_authorized_users(
    client_admin, client_epm, team_admin_feeder
):
    """Test to ensure user with proper permissions can retrieve feeders."""

    admin_result = client_admin.get("/api/v1/feeders")
    assert admin_result.data["_meta"]["count"] == 1
    assert admin_result.data["feeders"][0]["name"] == team_admin_feeder["name"]

    epm_result = client_epm.get("/api/v1/feeders")
    assert epm_result.data["_meta"]["count"] == 1
    assert epm_result.data["feeders"][0]["name"] == team_admin_feeder["name"]


def test_failure_get_feeder_unauthorized_users(
    client_user1, team_admin_feeder, team1_id
):
    """Test to ensure user w/o proper permissions can't retrieve other
    feeders."""

    user_result = client_user1.get("/api/v1/feeders")
    assert user_result.status_code == 200
    user_feeders = user_result.data["feeders"]
    for team_admin_feeder in user_feeders:
        assert team_admin_feeder["team_id"] == team1_id


def test_success_delete_feeder_authorized_users(
    client_admin, client_epm, team_admin_feeder, team1_id
):
    """Test to ensure user with proper permissions can delete feeders."""

    feeder_from_epm = {"name": "feeder-from-po", "team_id": team1_id}

    epm_result = client_epm.post("/api/v1/feeders", data=feeder_from_epm)
    feeder_from_po_id = epm_result.data["feeder"]["id"]
    feeder_from_po_etag = epm_result.headers.get("ETag")

    client_admin.delete(
        "/api/v1/feeders/%s" % team_admin_feeder["id"],
        headers={"If-match": team_admin_feeder["etag"]},
    )
    client_epm.delete(
        "/api/v1/feeders/%s" % feeder_from_po_id,
        headers={"If-match": feeder_from_po_etag},
    )

    admin_retrieve = client_admin.get("/api/v1/feeders/%s" % team_admin_feeder["id"])
    po_retrieve = client_epm.get("/api/v1/feeders/%s" % feeder_from_po_id)

    assert admin_retrieve.status_code == 404
    assert po_retrieve.status_code == 404


def test_failure_delete_feeder_unauthorized_users(client_user1, team_admin_feeder):
    """Test to ensure user w/o proper permissions can't delete feeders."""

    user_result = client_user1.delete(
        "/api/v1/feeders/%s" % team_admin_feeder["id"],
        headers={"If-match": team_admin_feeder["etag"]},
    )
    assert user_result.status_code == 401


def test_success_put_feeder_authorized_users(
    client_admin, client_epm, team_admin_feeder
):
    """Test to ensure user with proper permissions can update feeders."""

    client_admin.put(
        "/api/v1/feeders/%s" % team_admin_feeder["id"],
        data={"name": "newname"},
        headers={"If-match": team_admin_feeder["etag"]},
    )

    admin_result = client_admin.get("/api/v1/feeders/%s" % team_admin_feeder["id"])
    feeder_etag = admin_result.data["feeder"]["etag"]

    assert admin_result.data["feeder"]["name"] == "newname"

    client_epm.put(
        "/api/v1/feeders/%s" % team_admin_feeder["id"],
        data={"name": "newname-po"},
        headers={"If-match": feeder_etag},
    )

    epm_result = client_epm.get("/api/v1/feeders/%s" % team_admin_feeder["id"])

    assert epm_result.data["feeder"]["name"] == "newname-po"


def test_failure_put_feeder_unauthorized_users(client_user1, team_admin_feeder):
    """Test to ensure user w/o proper permissions can't update feeders."""

    user_result = client_user1.put(
        "/api/v1/feeders/%s" % team_admin_feeder["id"],
        data={"name": "newname"},
        headers={"If-match": team_admin_feeder["etag"]},
    )
    assert user_result.status_code == 401


def test_success_refresh_secret_feeder_authorized_users(
    client_admin, client_epm, team_admin_feeder
):
    """Test to ensure user with proper permissions can update feeders."""

    original_api_secret = team_admin_feeder["api_secret"]
    client_admin.put(
        "/api/v1/feeders/%s/api_secret" % team_admin_feeder["id"],
        headers={"If-match": team_admin_feeder["etag"]},
    )

    admin_result = client_admin.get("/api/v1/feeders/%s" % team_admin_feeder["id"])
    feeder_etag = admin_result.data["feeder"]["etag"]

    assert admin_result.data["feeder"]["api_secret"]
    assert admin_result.data["feeder"]["api_secret"] != original_api_secret

    original_api_secret = admin_result.data["feeder"]["api_secret"]
    client_epm.put(
        "/api/v1/feeders/%s/api_secret" % team_admin_feeder["id"],
        headers={"If-match": feeder_etag},
    )

    epm_result = client_epm.get("/api/v1/feeders/%s" % team_admin_feeder["id"])

    assert epm_result.data["feeder"]["api_secret"]
    assert epm_result.data["feeder"]["api_secret"] != original_api_secret


def test_failure_refresh_secret_feeder_unauthorized_users(
    client_user1, team_admin_feeder
):
    """Test to ensure user w/o proper permissions can't update feeders."""

    user_result = client_user1.put(
        "/api/v1/feeders/%s/api_secret" % team_admin_feeder["id"],
        data={"name": "newname"},
        headers={"If-match": team_admin_feeder["etag"]},
    )
    assert user_result.status_code == 401


def test_success_ensure_put_api_secret_is_not_leaked(client_admin, team_admin_feeder):
    """Test to ensure API secret is not leaked during update."""

    res = client_admin.put(
        "/api/v1/feeders/%s" % team_admin_feeder["id"],
        data={"name": "newname"},
        headers={"If-match": team_admin_feeder["etag"]},
    )

    assert res.status_code == 200
    assert "api_secret" not in res.data["feeder"]
