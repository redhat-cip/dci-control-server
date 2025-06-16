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


def test_success_create_product(client_admin):
    data = {
        "name": "New product",
        "label": "NEW_PRODUCT",
        "description": "New product description",
    }

    result = client_admin.post("/api/v1/products", data=data)

    assert result.status_code == 201
    assert result.data["product"]["name"] == data["name"]
    assert result.data["product"]["label"] == data["label"]
    assert result.data["product"]["description"] == data["description"]


def test_fail_create_permission_user(client_user1):
    data = {
        "name": "New product",
        "label": "NEW_PRODUCT",
        "description": "New product description",
    }

    result = client_user1.post("/api/v1/products", data=data)

    assert result.status_code == 401


def test_fail_ensure_payload_content_is_checked(client_admin):
    data = {
        "description": "name is missing",
    }

    result = client_admin.post("/api/v1/products", data=data)

    assert result.status_code == 400


def test_fail_create_product_already_exists(client_admin):
    data = {
        "name": "New product",
        "label": "NEW_PRODUCT",
        "description": "New product description",
    }

    result = client_admin.post("/api/v1/products", data=data)
    assert result.status_code == 201
    result = client_admin.post("/api/v1/products", data=data)
    assert result.status_code == 409


def test_success_update_product(client_admin, openstack_product):
    product_id = openstack_product["id"]

    url = "/api/v1/products/%s" % product_id
    assert openstack_product["name"] == "OpenStack"

    result = client_admin.put(
        url,
        data={"name": "New OpenStack", "label": "new-label"},
        headers={"If-match": openstack_product["etag"]},
    )
    assert result.status_code == 200
    assert result.data["product"]["name"] == "New OpenStack"
    assert result.data["product"]["label"] == "NEW-LABEL"
    assert (
        result.data["product"]["description"]
        == "OpenStack is a free and open-source software platform for cloud computing"
    )

    result = client_admin.put(
        url,
        data={"description": "new product"},
        headers={"If-match": result.data["product"]["etag"]},
    )
    assert result.status_code == 200
    assert result.data["product"]["name"] == "New OpenStack"
    assert result.data["product"]["description"] == "new product"


def test_success_get_all_products_admin(
    client_admin,
):
    result = client_admin.get("/api/v1/products")

    assert result.status_code == 200

    products = [r["label"] for r in result.data["products"]]
    assert ["OPENSHIFT", "OPENSTACK", "RHEL"] == sorted(products)


def test_success_get_all_products_user(
    client_admin, client_user1, openshift_product, team1_id
):
    result = client_user1.get("/api/v1/products")
    assert result.status_code == 200
    products = [r["label"] for r in result.data["products"]]
    assert ["OPENSTACK", "RHEL"] == sorted(products)

    respos = client_admin.post(
        "/api/v1/products/%s/teams" % openshift_product["id"],
        data={"team_id": team1_id},
    )
    assert respos.status_code == 201

    result = client_user1.get("/api/v1/products")
    assert result.status_code == 200
    products = [r["label"] for r in result.data["products"]]
    assert ["OPENSHIFT", "OPENSTACK", "RHEL"] == sorted(products)


def test_success_delete_product_admin(client_admin, rhel_product):
    result = client_admin.get("/api/v1/products")
    current_products = len(result.data["products"])

    result = client_admin.delete(
        "/api/v1/products/%s" % rhel_product["id"],
        headers={"If-match": rhel_product["etag"]},
    )

    assert result.status_code == 204

    result = client_admin.get("/api/v1/products")
    assert len(result.data["products"]) == current_products - 1

    result = client_admin.get("/api/v1/products/purge")
    assert len(result.data["products"]) == 1


def test_fail_delete_product_user(client_user1, rhel_product):
    result = client_user1.delete(
        "/api/v1/products/%s" % rhel_product["id"],
        headers={"If-match": rhel_product["etag"]},
    )

    assert result.status_code == 401


def test_success_get_products_embed(
    client_admin, client_user1, team1_id, openshift_product
):
    result = client_admin.get(
        "/api/v1/products/%s?embed=topics" % openshift_product["id"]
    )

    assert result.status_code == 200
    assert "topics" in result.data["product"].keys()

    result = client_user1.get(
        "/api/v1/products/%s?embed=topics" % openshift_product["id"]
    )
    assert result.status_code == 404
    result = client_admin.post(
        "api/v1/products/%s/teams" % openshift_product["id"],
        data={"team_id": team1_id},
    )
    assert result.status_code == 201

    result = client_user1.get(
        "/api/v1/products/%s?embed=topics" % openshift_product["id"]
    )
    assert result.status_code == 200
    assert "topics" in result.data["product"].keys()


def test_success_get_only_po_product(client_admin, client_epm, openstack_product):
    products_admin = client_admin.get("/api/v1/products").data
    assert len(products_admin["products"]) == 3
    products = [p["label"] for p in products_admin["products"]]
    assert ["OPENSHIFT", "OPENSTACK", "RHEL"] == sorted(products)

    products_po = client_epm.get("/api/v1/products").data
    assert len(products_po["products"]) == 3


def add_get_delete_team_to_product(caller, product, team_user_id):
    # create
    product_teams = caller.get("/api/v1/products/%s/teams" % product["id"])
    assert product_teams.status_code == 200
    nb_product_teams = len(product_teams.data["teams"])
    res = caller.post(
        "/api/v1/products/%s/teams" % product["id"], data={"team_id": team_user_id}
    )
    assert res.status_code == 201
    product_teams = caller.get("/api/v1/products/%s/teams" % product["id"])
    new_nb_product_teams = len(product_teams.data["teams"])
    assert product_teams.status_code == 200
    assert new_nb_product_teams == (nb_product_teams + 1)
    teams_ids = {t["id"] for t in product_teams.data["teams"]}
    assert team_user_id in teams_ids

    # delete
    delete_team = caller.delete(
        "/api/v1/products/%s/teams/%s" % (product["id"], team_user_id)
    )
    assert delete_team.status_code == 204
    product_teams = caller.get("/api/v1/products/%s/teams" % product["id"])
    assert product_teams.status_code == 200
    teams_ids = {t["id"] for t in product_teams.data["teams"]}
    assert team_user_id not in teams_ids


def test_add_get_delete_team_to_product(
    client_admin, client_epm, openshift_product, team1_id
):
    # as admin
    add_get_delete_team_to_product(client_admin, openshift_product, team1_id)
    # as product owner
    add_get_delete_team_to_product(client_epm, openshift_product, team1_id)


def test_add_get_delete_team_to_product_as_user(client_user1, rhel_product, team1_id):
    # create
    product_teams = client_user1.get("/api/v1/products/%s/teams" % rhel_product["id"])
    assert product_teams.status_code == 401
    res = client_user1.post(
        "/api/v1/products/%s/teams" % rhel_product["id"], data={"team_id": team1_id}
    )
    assert res.status_code == 401
    product_teams = client_user1.get("/api/v1/products/%s/teams" % rhel_product["id"])
    assert product_teams.status_code == 401

    # delete
    delete_team = client_user1.delete(
        "/api/v1/products/%s/teams/%s" % (rhel_product["id"], team1_id)
    )
    assert delete_team.status_code == 401
