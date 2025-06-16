# -*- encoding: utf-8 -*-
#
# Copyright 2015-2016 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from dci import auth
from dci import dci_config

import mock
import datetime


def test_api_with_unauthorized_credentials(client_unauthorized, rhel_80_topic_id):
    assert (
        client_unauthorized.get(
            "/api/v1/topics/%s/components" % rhel_80_topic_id
        ).status_code
        == 401
    )
    assert client_unauthorized.get("/api/v1/jobs").status_code == 401
    assert client_unauthorized.get("/api/v1/remotecis").status_code == 401
    assert client_unauthorized.get("/api/v1/teams").status_code == 401
    assert client_unauthorized.get("/api/v1/users").status_code == 401
    assert client_unauthorized.get("/api/v1/topics")


def test_admin_required_success_when_admin(client_admin):
    assert client_admin.post("/api/v1/teams", data={"name": "team"}).status_code == 201


def test_admin_required_fail_when_not_admin(client_user1):
    assert client_user1.post("/api/v1/teams", data={"name": "team"}).status_code == 401


# mock datetime so that the token is now considered as expired
@mock.patch("jwt.api_jwt.datetime", spec=datetime.datetime)
def test_decode_jwt(m_datetime, access_token):
    pubkey = dci_config.CONFIG["SSO_PUBLIC_KEY"]
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime.fromtimestamp(
        1505564918
    ).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    decoded_jwt = auth.decode_jwt(access_token, pubkey, "dci")
    assert decoded_jwt["username"] == "dci"
    assert decoded_jwt["email"] == "dci@distributed-ci.io"


def test_jwk_to_pem():
    jwk = {
        "kid": "qb5l0vn-jKtkqXAB5Aa63S2oMqA2OeEkYrzNJQj1oJ8",
        "kty": "RSA",
        "alg": "RS256",
        "use": "sig",
        "n": "6ZafME0khw-kLle3zAqER-Nmyd3QdVCqMoZbJo2kquq4nhP26uY1ldSTw3P0OucmbLCUz0OY25aPMJCWKiRQrlrnYOLzFpYxxGTlon8U3ZGrPrc-hTJkGV0u9YpPWOSrfO-nXKHOBp33w-o1Kii-Xb3AmMbBFiMD7A5djeKGxPiK7SKwMTrZNkvmfDc0jtnUXjgpTjhOP21ERZw3n6D6BEbvzOlY2gkdUM8O1tJ0VBkfBE3izp6q2JTPdnhyBMRnEqzmRs3AdIO2QkoP7uDKK-JiQuDvFZDl3WhkHD_kauzledSwvNgGCtANzD-GsscC1i5ITNbV-20Xb3kRytcVKfVWCKdC8SsAebF0nNt--gpGF8GwYifiHYdKe1gewx7urfZi3-GvDFyVNUIXW5nz74zJ0bLA_-hkunQnJG9H21c3oRBm6zpf_W-2vhiUYL8WWtPfe3STIqzAad_2TjhTx4FWdrG9TJFhE_4Wm7tw4SC28G1qTLJmDip8MOUA7y8RpHRkN2em7b76ehDra5xj4f7GnP6F6fJPJG8l-WQD6Gcc5fymOYYE7-rrdNTL24frA8RAFiOL7A7hLvXuKq5hccbSE_gBR91Z33gIk5t1SlTThZsTH7k846NUb9IIBrnuvD-cA75IajDRSu_XdXYpgdrmGGP1kN7df1WCrLioHTE",
        "e": "AQAB",
        "x5c": [
            "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"
        ],
        "x5t": "ZJQIZXhuQm6qkQIItxGt5EC7lrE",
        "x5t#S256": "7O0oHs6s4NkwL2TvggfPmOtiHD_Z5R300jJSA94nkfM",
    }
    assert (
        auth.jwk_to_pem(jwk)
        == b"""-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEA6ZafME0khw+kLle3zAqE
R+Nmyd3QdVCqMoZbJo2kquq4nhP26uY1ldSTw3P0OucmbLCUz0OY25aPMJCWKiRQ
rlrnYOLzFpYxxGTlon8U3ZGrPrc+hTJkGV0u9YpPWOSrfO+nXKHOBp33w+o1Kii+
Xb3AmMbBFiMD7A5djeKGxPiK7SKwMTrZNkvmfDc0jtnUXjgpTjhOP21ERZw3n6D6
BEbvzOlY2gkdUM8O1tJ0VBkfBE3izp6q2JTPdnhyBMRnEqzmRs3AdIO2QkoP7uDK
K+JiQuDvFZDl3WhkHD/kauzledSwvNgGCtANzD+GsscC1i5ITNbV+20Xb3kRytcV
KfVWCKdC8SsAebF0nNt++gpGF8GwYifiHYdKe1gewx7urfZi3+GvDFyVNUIXW5nz
74zJ0bLA/+hkunQnJG9H21c3oRBm6zpf/W+2vhiUYL8WWtPfe3STIqzAad/2TjhT
x4FWdrG9TJFhE/4Wm7tw4SC28G1qTLJmDip8MOUA7y8RpHRkN2em7b76ehDra5xj
4f7GnP6F6fJPJG8l+WQD6Gcc5fymOYYE7+rrdNTL24frA8RAFiOL7A7hLvXuKq5h
ccbSE/gBR91Z33gIk5t1SlTThZsTH7k846NUb9IIBrnuvD+cA75IajDRSu/XdXYp
gdrmGGP1kN7df1WCrLioHTECAwEAAQ==
-----END PUBLIC KEY-----
"""
    )
