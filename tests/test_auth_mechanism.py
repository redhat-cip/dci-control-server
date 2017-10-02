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

from datetime import datetime
import pytest

from dci.auth_mechanism import BasicAuthMechanism
from dci.auth_mechanism import SignatureAuthMechanism


class MockRequest(object):
    def __init__(self, auth=None):
        self.authorization = auth


class AuthMock(object):
    def __init__(self):
        self.username = 'test'
        self.password = 'password'


def test_basic_auth_mecanism_is_valid_false_if_no_auth():
    basic_auth_mecanism = BasicAuthMechanism(MockRequest())
    assert not basic_auth_mecanism.is_valid()


def test_bam_is_valid_false_if_not_authenticated():
    def return_is_authenticated(*args):
        return {}, False

    basic_auth_mecanism = BasicAuthMechanism(MockRequest(AuthMock()))
    basic_auth_mecanism.get_user_and_check_auth = return_is_authenticated
    assert not basic_auth_mecanism.is_valid()


def test_bam_is_valid():
    def return_is_authenticated(*args):
        return {}, True

    def return_get_user_teams(*args):
        return []

    basic_auth_mecanism = BasicAuthMechanism(MockRequest(AuthMock()))
    basic_auth_mecanism.get_user_and_check_auth = return_is_authenticated
    basic_auth_mecanism.get_user_teams = return_get_user_teams
    assert basic_auth_mecanism.is_valid()


class MockSignedRequest(object):
    def __init__(self, headers={}):
        self.headers = headers


class RemoteCiMock(object):
    def __init__(self, id, api_secret='dummy',
                 team_id='90b89be5-141d-4866-bb4d-248694d95445'):
        self.id = id
        self.api_secret = api_secret
        self.team_id = team_id

    def __iter__(self):
        yield 'team_id', self.team_id


sam_headers = {
    'DCI-Client-Info': '2016-12-12 03:03:03Z/remoteci/Morbo',
    'DCI-Auth-Signature': 'DOOOOOOOM!!!',
}


def return_get_remoteci(*args):
    return RemoteCiMock(args[0])


def _test_client_info_value(client_info_value):
    mech = SignatureAuthMechanism(
        MockSignedRequest({
            'DCI-Client-Info': client_info_value,
            'DCI-Auth-Signature': None,
        }))
    return mech.get_client_info()


def test_get_client_info_bad():
    bad_format_message = \
        'DCI-Client-Info should match the following format: ' + \
        '"YYYY-MM-DD HH:MI:SSZ/<client_type>/<id>"'

    with pytest.raises(ValueError) as e_info:
        _test_client_info_value('pif!paf!pouf!')
    assert e_info.value.args[0] == bad_format_message

    with pytest.raises(ValueError) as e_info:
        _test_client_info_value('pif/paf')
    assert e_info.value.args[0] == bad_format_message

    with pytest.raises(ValueError) as e_info:
        _test_client_info_value('pif/paf/pouf/.')
    assert e_info.value.args[0] == bad_format_message

    with pytest.raises(ValueError) as e_info:
        _test_client_info_value('p/p/')
    assert e_info.value.args[0] == bad_format_message

    with pytest.raises(ValueError) as e_info:
        _test_client_info_value('p//p')
    assert e_info.value.args[0] == bad_format_message

    with pytest.raises(ValueError) as e_info:
        _test_client_info_value('pif/paf/pouf')


def test_get_client_info_good():
    expected = {
        'timestamp': datetime(2016, 3, 21, 15, 37, 59),
        'type': 'foo',
        'id': '12890-abcdef',
    }
    client_info_value = '2016-03-21 15:37:59Z/foo/12890-abcdef'

    assert _test_client_info_value(client_info_value) == expected


def test_sam_is_valid_false_if_no_signature():
    mech = SignatureAuthMechanism(MockSignedRequest())
    assert not mech.is_valid()


def test_sam_is_valid_false_if_not_authenticated():
    def return_is_authenticated(*args):
        return False

    mech = SignatureAuthMechanism(MockSignedRequest(sam_headers))
    mech.verify_remoteci_auth_signature = return_is_authenticated
    mech.get_remoteci = return_get_remoteci
    assert not mech.is_valid()


def test_sam_is_valid():
    def return_is_authenticated(*args):
        return True

    mech = SignatureAuthMechanism(MockSignedRequest(sam_headers))
    mech.verify_remoteci_auth_signature = return_is_authenticated
    mech.get_remoteci = return_get_remoteci
    assert mech.is_valid()
