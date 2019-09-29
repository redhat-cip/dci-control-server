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
import pytest

from OpenSSL.crypto import load_certificate, FILETYPE_PEM


@pytest.fixture
def RHELProduct(admin):
    data = {"name": "RHEL", "label": "RHEL", "description": "Red Hat Entreprise Linux"}
    return admin.post("/api/v1/products", data=data).data["product"]


@pytest.fixture
def RHEL80Topic(admin, RHELProduct):
    data = {
        "name": "RHEL-8.0",
        "product_id": RHELProduct["id"],
        "component_types": ["Compose"],
        "export_control": True,
    }
    return admin.post("/api/v1/topics", data=data).data["topic"]


@pytest.fixture
def RHEL80Component(admin, RHEL80Topic):
    data = {
        "topic_id": RHEL80Topic["id"],
        "name": "RHEL-8.0.0-20190926.n.0",
        "type": "Compose",
    }
    return admin.post("/api/v1/components", data=data).data["component"]


@pytest.fixture
def RHEL81Topic(admin, RHELProduct):
    data = {
        "name": "RHEL-8.1",
        "product_id": RHELProduct["id"],
        "component_types": ["Compose"],
        "export_control": False,
    }
    return admin.post("/api/v1/topics", data=data).data["topic"]


@pytest.fixture
def RHEL81Component(admin, RHEL81Topic):
    data = {
        "topic_id": RHEL81Topic["id"],
        "name": "RHEL-8.1.0-20190926.n.0",
        "type": "Compose",
    }
    return admin.post("/api/v1/components", data=data).data["component"]


def get_certificate_headers(remoteci_context, remoteci, product, topic, component):
    keys = remoteci_context.put(
        "/api/v1/remotecis/%s/keys" % remoteci["id"],
        headers={"If-match": remoteci["etag"]},
    ).data["keys"]
    cert = load_certificate(FILETYPE_PEM, keys["cert"])
    fingerprint = cert.digest("sha1").decode("utf-8").lower().replace(":", "")
    return {
        "SSLVerify": "SUCCESS",
        "SSLFingerprint": fingerprint,
        "X-Original-URI": "%s/%s/%s/" % (product["id"], topic["id"], component["id"]),
    }


def test_user_cert_verified_if_user_team_in_RHEL_export_control_true(
    admin, remoteci_context, remoteci, RHELProduct, RHEL80Topic,
    RHEL80Component, cakeys
):
    certificate_headers = get_certificate_headers(
        remoteci_context, remoteci, RHELProduct, RHEL80Topic, RHEL80Component
    )
    request = admin.get("/api/v1/certs/verify", headers=certificate_headers)
    assert request.status_code == 403
    request = admin.post(
        "/api/v1/products/%s/teams" % RHELProduct["id"],
        data={"team_id": remoteci["team_id"]},
    )
    assert request.status_code == 201
    request = admin.get("/api/v1/certs/verify", headers=certificate_headers)
    assert request.status_code == 200


def test_user_cert_verified_if_user_team_in_RHEL_export_control_false(
    admin, remoteci_context, remoteci, RHELProduct, RHEL81Topic,
    RHEL81Component, cakeys
):
    certificate_headers = get_certificate_headers(
        remoteci_context, remoteci, RHELProduct, RHEL81Topic, RHEL81Component
    )
    request = admin.get("/api/v1/certs/verify", headers=certificate_headers)
    assert request.status_code == 403
    admin.post(
        "/api/v1/products/%s/teams" % RHELProduct["id"],
        data={"team_id": remoteci["team_id"]},
    )
    request = admin.get("/api/v1/certs/verify", headers=certificate_headers)
    assert request.status_code == 403
    admin.post(
        "/api/v1/topics/%s/teams" % RHEL81Topic['id'],
        data={"team_id": remoteci["team_id"]}
    )
    request = admin.get("/api/v1/certs/verify", headers=certificate_headers)
    assert request.status_code == 200


def test_user_cert_verified_if_user_team_in_RHEL81(
    admin, remoteci_context, remoteci, RHELProduct, RHEL81Topic,
    RHEL81Component, cakeys
):
    certificate_headers = get_certificate_headers(
        remoteci_context, remoteci, RHELProduct, RHEL81Topic, RHEL81Component
    )
    request = admin.get("/api/v1/certs/verify", headers=certificate_headers)
    assert request.status_code == 403
    admin.post(
        "/api/v1/products/%s/teams" % RHELProduct["id"],
        data={"team_id": remoteci["team_id"]},
    )
    admin.post(
        "/api/v1/topics/%s/teams" % RHEL81Topic["id"],
        data={"team_id": remoteci["team_id"]},
    )
    request = admin.get("/api/v1/certs/verify", headers=certificate_headers)
    assert request.status_code == 200
