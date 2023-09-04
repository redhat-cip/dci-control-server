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


def test_success_create_product(admin):
    data = {
        "name": "New product",
        "label": "NEW_PRODUCT",
        "description": "New product description",
    }

    result = admin.post("/api/v1/products", data=data)

    assert result.status_code == 201
    assert result.data["product"]["name"] == data["name"]
    assert result.data["product"]["label"] == data["label"]
    assert result.data["product"]["description"] == data["description"]


def test_fail_create_permission_user(user):
    data = {
        "name": "New product",
        "label": "NEW_PRODUCT",
        "description": "New product description",
    }

    result = user.post("/api/v1/products", data=data)

    assert result.status_code == 401


def test_fail_ensure_payload_content_is_checked(admin):
    data = {
        "description": "name is missing",
    }

    result = admin.post("/api/v1/products", data=data)

    assert result.status_code == 400


def test_fail_create_product_already_exists(admin):
    data = {
        "name": "New product",
        "label": "NEW_PRODUCT",
        "description": "New product description",
    }

    result = admin.post("/api/v1/products", data=data)
    assert result.status_code == 201
    result = admin.post("/api/v1/products", data=data)
    assert result.status_code == 409


def test_success_update_product(admin, openstack_product):
    product_id = openstack_product["id"]

    url = "/api/v1/products/%s" % product_id
    assert openstack_product["name"] == "OpenStack"

    result = admin.put(
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

    result = admin.put(
        url,
        data={"description": "new product"},
        headers={"If-match": result.data["product"]["etag"]},
    )
    assert result.status_code == 200
    assert result.data["product"]["name"] == "New OpenStack"
    assert result.data["product"]["description"] == "new product"


def test_success_get_all_products_admin(
    admin,
):
    result = admin.get("/api/v1/products")

    assert result.status_code == 200

    products = [r["label"] for r in result.data["products"]]
    assert ["OPENSHIFT", "OPENSTACK", "RHEL"] == sorted(products)


def test_success_get_all_products_user(admin, user, openshift_product, team_user_id):
    result = user.get("/api/v1/products")
    assert result.status_code == 200
    products = [r["label"] for r in result.data["products"]]
    assert ["OPENSTACK", "RHEL"] == sorted(products)

    respos = admin.post(
        "/api/v1/products/%s/teams" % openshift_product["id"],
        data={"team_id": team_user_id},
    )
    assert respos.status_code == 201

    result = user.get("/api/v1/products")
    assert result.status_code == 200
    products = [r["label"] for r in result.data["products"]]
    assert ["OPENSHIFT", "OPENSTACK", "RHEL"] == sorted(products)


def test_success_delete_product_admin(admin, product):
    result = admin.get("/api/v1/products")
    current_products = len(result.data["products"])

    result = admin.delete(
        "/api/v1/products/%s" % product["id"], headers={"If-match": product["etag"]}
    )

    assert result.status_code == 204

    result = admin.get("/api/v1/products")
    assert len(result.data["products"]) == current_products - 1

    result = admin.get("/api/v1/products/purge")
    assert len(result.data["products"]) == 1


def test_fail_delete_product_user(user, product):
    result = user.delete(
        "/api/v1/products/%s" % product["id"], headers={"If-match": product["etag"]}
    )

    assert result.status_code == 401


def test_success_get_products_embed(admin, user, team_user_id, openshift_product):
    result = admin.get("/api/v1/products/%s?embed=topics" % openshift_product["id"])

    assert result.status_code == 200
    assert "topics" in result.data["product"].keys()

    result = user.get("/api/v1/products/%s?embed=topics" % openshift_product["id"])
    assert result.status_code == 404
    result = admin.post(
        "api/v1/products/%s/teams" % openshift_product["id"],
        data={"team_id": team_user_id},
    )
    assert result.status_code == 201

    result = user.get("/api/v1/products/%s?embed=topics" % openshift_product["id"])
    assert result.status_code == 200
    assert "topics" in result.data["product"].keys()


def test_success_get_only_po_product(admin, epm, openstack_product):
    products_admin = admin.get("/api/v1/products").data
    assert len(products_admin["products"]) == 3
    products = [p["label"] for p in products_admin["products"]]
    assert ["OPENSHIFT", "OPENSTACK", "RHEL"] == sorted(products)

    products_po = epm.get("/api/v1/products").data
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


def test_add_get_delete_team_to_product(admin, epm, openshift_product, team_user_id):
    # as admin
    add_get_delete_team_to_product(admin, openshift_product, team_user_id)
    # as product owner
    add_get_delete_team_to_product(epm, openshift_product, team_user_id)


def test_add_get_delete_team_to_product_as_user(user, product, team_user_id):
    # create
    product_teams = user.get("/api/v1/products/%s/teams" % product["id"])
    assert product_teams.status_code == 401
    res = user.post(
        "/api/v1/products/%s/teams" % product["id"], data={"team_id": team_user_id}
    )
    assert res.status_code == 401
    product_teams = user.get("/api/v1/products/%s/teams" % product["id"])
    assert product_teams.status_code == 401

    # delete
    delete_team = user.delete(
        "/api/v1/products/%s/teams/%s" % (product["id"], team_user_id)
    )
    assert delete_team.status_code == 401
