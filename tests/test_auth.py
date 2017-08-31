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

import mock
import datetime


def test_api_with_unauthorized_credentials(unauthorized, topic_id):
    assert unauthorized.get(
        '/api/v1/topics/%s/components' % topic_id).status_code == 401
    assert unauthorized.get('/api/v1/jobs').status_code == 401
    assert unauthorized.get('/api/v1/jobstates').status_code == 401
    assert unauthorized.get('/api/v1/remotecis').status_code == 401
    assert unauthorized.get('/api/v1/teams').status_code == 401
    assert unauthorized.get(
        '/api/v1/topics/%s/tests' % topic_id).status_code == 401
    assert unauthorized.get('/api/v1/users').status_code == 401
    assert unauthorized.get('/api/v1/files').status_code == 401
    assert unauthorized.get('/api/v1/topics')


def test_admin_required_success_when_admin(admin):
    assert admin.post('/api/v1/teams',
                      data={'name': 'team'}).status_code == 201


def test_admin_required_fail_when_not_admin(user):
    assert user.post('/api/v1/teams', data={'name': 'team'}).status_code == 401


# Keycloak test public key
_pubkey = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAgBH5yRAVT3gkOyUXMIVn
wSB6L/gurcAIAr4OIg83rduY8v7JGG3FL30bFr38dRGBQCWGDUqzeSRg0KVtfUk0
r01CTa8WDvj/A35P8ANhYjZQb6Rx2ibyhTwnm4QSVLeBe424M8ybRgRl9WkAixRO
iNNF2o9uNWJkTFLZ8wCGnYcu/PI8ZQCi/PnFjF+r63id8VOG5eSDrTLZuqbs9L0L
L4w3+R8tgTIUWl2X/Fps760XYl9r3WjAXc8aYiLPqYR6EheoC00QZmGxRbdq8yVt
csnCpzVVAEEaQEwv/Smu9e1L2ObyAp387xjDOTHQZNXMb7TSJuhxyOLQQ3NWO+1o
zQIDAQAB
-----END PUBLIC KEY-----
"""


# mock datetime so that the token is now considered as expired
@mock.patch('jwt.api_jwt.datetime', spec=datetime.datetime)
def test_decode_jwt(m_datetime):
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime.\
        fromtimestamp(1505564918).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    access_token = 'eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICItNjhX' \
        'OHFidDV6dGxWdjRnZW1FV0t3TWVaUUxWYnMzQUxWZTRrTlhkVDhFIn0.eyJqdGkiOiJ' \
        'iZmZmMTI5YS1mN2YwLTQ3NWUtOWRmNC1mMTU3ZjJmNzhiYTciLCJleHAiOjE1MDU1Nj' \
        'U3MTgsIm5iZiI6MCwiaWF0IjoxNTA1NTY0ODE4LCJpc3MiOiJodHRwOi8vbG9jYWxob' \
        '3N0OjgxODAvYXV0aC9yZWFsbXMvZGNpLXRlc3QiLCJhdWQiOiJkY2ktY3MiLCJzdWIi' \
        'OiJiMzA5ZTRkYS1lZDZmLTQ1ZmMtOTA1NC03ODU1ZTZlNGViOTIiLCJ0eXAiOiJCZWF' \
        'yZXIiLCJhenAiOiJkY2ktY3MiLCJub25jZSI6ImFiNDBlZGJhLTkxODctMTFlNy1hOT' \
        'IxLWM4NWI3NjM2YzMzZiIsImF1dGhfdGltZSI6MTUwNTU2NDgxOCwic2Vzc2lvbl9zd' \
        'GF0ZSI6ImM1ZjY4OWM4LTY2YWQtNDFjYy1iNzA0LTRkNWZmOTQyNzE1MiIsImFjciI6' \
        'IjEiLCJhbGxvd2VkLW9yaWdpbnMiOlsiaHR0cDovL2xvY2FsaG9zdDo1MDAwIl0sInJ' \
        'lYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3' \
        'VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiL' \
        'CJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sImVtYWlsIjoi' \
        'ZGNpQGRpc3RyaWJ1dGVkLWNpLmlvIiwidXNlcm5hbWUiOiJkY2kifQ.Sv-r1bChnDLQ' \
        'I1S9j07UJ3nYInu0grJS6_tCznLG2gW3_QXQhpLNKiMpNlyJU7hDQHXmRG7d2Y58JXF' \
        'RPLgDFMGnUeTyGxSJS2PcZ6WKKDLMdOnfqexKJfSqU17jJ7h18qeRjLWdK-PMLJAQkJ' \
        'u9QlqaQsZNIXH_2uYY1_rWeaulPia_fj6iNzmYxeUvqci2IBbRIrZV5lvxlL55v1siG' \
        '4vF26G8pbjGL7Fg7HvDekJCTZE5uWRCQtg15IJ44Fsspip6C2kSIhAFvsitFe5r7ltO' \
        'Nnh5nbZCsru5r9qEEYzcSyIZnkyVGgZrxNY_PY8CC6WtSBZTC7inFFcWWKioSw'
    decoded_jwt = auth.decode_jwt(access_token, _pubkey, 'dci-cs')
    assert decoded_jwt['username'] == 'dci'
    assert decoded_jwt['email'] == 'dci@distributed-ci.io'
