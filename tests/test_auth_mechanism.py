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
