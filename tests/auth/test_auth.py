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


def test_api_with_unauthorized_credentials(unauthorized, topic_id):
    assert unauthorized.get(
        '/api/v1/topics/%s/components' % topic_id).status_code == 401
    assert unauthorized.get('/api/v1/jobs').status_code == 401
    assert unauthorized.get('/api/v1/remotecis').status_code == 401
    assert unauthorized.get('/api/v1/teams').status_code == 401
    assert unauthorized.get('/api/v1/users').status_code == 401
    assert unauthorized.get('/api/v1/topics')


def test_admin_required_success_when_admin(admin):
    assert admin.post('/api/v1/teams',
                      data={'name': 'team'}).status_code == 201


def test_admin_required_fail_when_not_admin(user):
    assert user.post('/api/v1/teams', data={'name': 'team'}).status_code == 401


# mock datetime so that the token is now considered as expired
@mock.patch('jwt.api_jwt.datetime', spec=datetime.datetime)
def test_decode_jwt(m_datetime, access_token):
    pubkey = dci_config.CONFIG['SSO_PUBLIC_KEY']
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime.\
        fromtimestamp(1505564918).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    decoded_jwt = auth.decode_jwt(access_token, pubkey, 'dci')
    assert decoded_jwt['username'] == 'dci'
    assert decoded_jwt['email'] == 'dci@distributed-ci.io'
