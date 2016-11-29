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
    basic_auth_mecanism.build_auth = return_is_authenticated
    assert not basic_auth_mecanism.is_valid()


def test_bam_is_valid():
    def return_is_authenticated(*args):
        return {}, True

    basic_auth_mecanism = BasicAuthMechanism(MockRequest(AuthMock()))
    basic_auth_mecanism.build_auth = return_is_authenticated
    assert basic_auth_mecanism.is_valid()


class MockSignedRequest(object):
    def __init__(self, headers={}):
        self.headers = headers


sam_headers = {
    'DCI-Client-ID': '2016-12-12 03:03:03Z/remoteci/Morbo',
    'DCI-Auth-Signature': 'DOOOOOOOM!!!',
}


def test_sam_is_valid_false_if_no_signature():
    signature_auth_mechanism = SignatureAuthMechanism(MockSignedRequest())
    assert not signature_auth_mechanism.is_valid()


def test_sam_is_valid_false_if_not_authenticated():
    def return_is_authenticated(*args):
        return {}, False

    signature_auth_mechanism = SignatureAuthMechanism(
        MockSignedRequest(sam_headers))
    signature_auth_mechanism._verify_remoteci_auth_signature = \
        return_is_authenticated
    assert not signature_auth_mechanism.is_valid()


def test_sam_is_valid():
    def return_is_authenticated(*args):
        return {}, True

    signature_auth_mechanism = SignatureAuthMechanism(
        MockSignedRequest(sam_headers))
    signature_auth_mechanism._verify_remoteci_auth_signature = \
        return_is_authenticated
    signature_auth_mechanism._get_remoteci
    assert signature_auth_mechanism.is_valid()
