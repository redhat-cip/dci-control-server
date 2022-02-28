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

import dci.auth_mechanism as authm
from dci.common import exceptions as dci_exc
from dci.db import models2
from dci import auth
from tests import utils

import pytest


class MockRequest(object):
    def __init__(self, auth=None):
        self.authorization = auth


class AuthMock(object):
    def __init__(self):
        self.username = "test"
        self.password = "password"


def test_basic_auth_mecanism_authenticate_fail_if_no_auth():
    basic_auth_mecanism = authm.BasicAuthMechanism(MockRequest())
    with pytest.raises(dci_exc.DCIException):
        basic_auth_mecanism.authenticate()


def test_bam_authenticate_fail_if_not_authenticated():
    def return_is_authenticated(*args):
        return {}, False

    basic_auth_mecanism = authm.BasicAuthMechanism(MockRequest(AuthMock()))
    basic_auth_mecanism.get_user_and_check_auth = return_is_authenticated
    with pytest.raises(dci_exc.DCIException):
        basic_auth_mecanism.authenticate()


def test_bam_authenticate():
    def return_is_authenticated(*args):
        return {}, True

    basic_auth_mecanism = authm.BasicAuthMechanism(MockRequest(AuthMock()))
    basic_auth_mecanism.get_user_and_check_auth = return_is_authenticated
    assert basic_auth_mecanism.authenticate()


def test_nrt_one_user_s_name_is_equal_to_the_email_of_another_user(session, app):
    session.add(
        models2.User(
            name="user3@example.org",
            sso_username="user3@example.org",
            fullname="user3@example.org",
            password=auth.hash_password("user3@example.org"),
            email="user4@example.org",
        )
    )
    session.add(
        models2.User(
            name="user4@example.org",
            sso_username="user4@example.org",
            fullname="user4@example.org",
            password=auth.hash_password("user4@example.org"),
            email="user3@example.org",
        )
    )
    session.commit()
    user = utils.generate_client(app, ("user3@example.org", "user3@example.org"))
    assert user.get("/api/v1/identity").status_code == 200
