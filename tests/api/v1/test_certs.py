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
from OpenSSL.crypto import load_certificate, FILETYPE_PEM


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
    admin, remoteci_context, remoteci, RHELProduct, RHEL80Topic, RHEL80Component, cakeys
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
    admin, remoteci_context, remoteci, RHELProduct, RHEL81Topic, RHEL81Component, cakeys
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
        "/api/v1/topics/%s/teams" % RHEL81Topic["id"],
        data={"team_id": remoteci["team_id"]},
    )
    request = admin.get("/api/v1/certs/verify", headers=certificate_headers)
    assert request.status_code == 200


def test_user_cert_verified_if_user_team_in_RHEL81(
    admin, remoteci_context, remoteci, RHELProduct, RHEL81Topic, RHEL81Component, cakeys
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


def test_remoteci_cert_still_valid(remoteci_context, remoteci_user_id):
    r = remoteci_context.get("/api/v1/remotecis/%s" % remoteci_user_id)
    keys = remoteci_context.put(
        "/api/v1/remotecis/%s/keys" % remoteci_user_id,
        headers={"If-match": r.data["remoteci"]["etag"]},
    ).data["keys"]
    valid = remoteci_context.post(
        "/api/v1/certs/check",
        data={"cert": keys["cert"]},
    )
    assert valid.status_code == 204

    old_cert = """-----BEGIN CERTIFICATE-----
MIIEXjCCAkYCAgPoMA0GCSqGSIb3DQEBCwUAMIGHMQswCQYDVQQGEwJGUjEMMAoG
A1UECAwDSURGMQ4wDAYDVQQHDAVQYXJpczEPMA0GA1UECgwGUmVkSGF0MQwwCgYD
VQQLDANEQ0kxETAPBgNVBAMMCERDSS1SZXBvMSgwJgYJKoZIhvcNAQkBFhlkaXN0
cmlidXRlZC1jaUByZWRoYXQuY29tMB4XDTIwMDgyNjA5MDAwN1oXDTMwMDgyNDA5
MDAwN1owYTELMAkGA1UEBhMCRlIxDDAKBgNVBAgMA0lERjEOMAwGA1UEBwwFUGFy
aXMxDzANBgNVBAoMBlJlZEhhdDEMMAoGA1UECwwDRENJMRUwEwYDVQQDDAxEQ0kt
cmVtb3RlQ0kwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDTZNTs8oMV
LDrDWv2nxSzhRxY5geelpeuuwMqFze6GCa1l8QsF+XJuBAFNoCmfKOvBUgRpr71b
dnyL4yZgeSvMVjLsbyZlW7WAPuZb88UY03tGXOu7altuxSRXvthhyfJRhIjF2vdM
BYcJpAgKRb+tutDHMOmRLHOKdg+EDYFh7CA8AUalQ7LckYa27TH36T5LdoemP8ws
LzvH94kBrYDHhkhwoXp2n3p9yxz48tckPCSO8z8D7fHLJvByvPDJccffExi5LG+r
h5XF87yZzC2vdVyxu+wfbEkAIlI3GUvaw6s7d0/DSGhDZjq4ghRePUnq1ZbHqM0a
dKl6rnB/lA4rAgMBAAEwDQYJKoZIhvcNAQELBQADggIBADo/ZLJiT/0ZcPxaFboK
ALGZfokGbs60Z4baPymHmP+dwkaP9csL0NiB8lKACBSo4ZCPBh6x/Vn9JQ2pREk0
X4YyM2BA6yyqUTK2LwHvFeMWit38sS009dHv765n669ITzC0VXtZQzbmaad1mPCr
cQW/wHmlSk5mvtBY/LW210vQ9suVTDCqiSao6ZNNSIRvoOF+qRXiRkH1i+H4oudL
pBOB0VhTLqQY2RTyPPjRxHWseoKLnRhsMFejq9wl+bPy0quW5yWFQZIm4GBjs+xH
QlIiJ8MzblZKU456XqCGClhyrgevPnUcarmj/AIW64yoPUlJBXplmCsBCnsfE2iv
9gawCHtBGHG42G5awB7ZlxkjM8IWZXiwfFED8TUNoQyFVKHI9C+Hu2FwBLgxLpGu
0c3LZt7kXvpoJQORl0/0IGFfyEAICFtzMFsU1njTsNA/h50auZPwALfkl2sRugG2
b8EzcU9bjwiASlgPow40Y0H0WCA0pyihkTqC9X8QrJ1D16ZmyS0TMyvw6N8Bc5oQ
U0WSg4zXl7Rh1S/C7qNbQR9mj2FMtTOHoxNSnm2dpBYais7Jps/H+UQ3eiXa8jwm
2he44lnFUOGm02y8lOpD+ooY/It5OH4FqKUYgwrn9awp9AaxYRSt6e/++gSEyV0C
P+qMxItk46BMfaEd8MLttHkJ
-----END CERTIFICATE-----"""
    valid = remoteci_context.post(
        "/api/v1/certs/check",
        data={"cert": old_cert},
    )
    assert valid.status_code == 403


def test_user_cant_verify_cert(user, remoteci_user_id):
    r = user.get("/api/v1/remotecis/%s" % remoteci_user_id)
    keys = user.put(
        "/api/v1/remotecis/%s/keys" % remoteci_user_id,
        headers={"If-match": r.data["remoteci"]["etag"]},
    ).data["keys"]
    valid = user.post(
        "/api/v1/certs/check",
        data={"cert": keys["cert"]},
    )
    assert valid.status_code == 400
