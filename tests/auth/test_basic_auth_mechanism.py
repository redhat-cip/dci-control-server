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

from dci.db import models2
from dci import auth
from tests import utils


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


def test_user_without_password_cannot_basic_auth(session, app):
    session.add(
        models2.User(
            name="nopassword@example.org",
            sso_username="nopassword@example.org",
            fullname="nopassword@example.org",
            password=None,
            email="nopassword@example.org",
        )
    )
    session.commit()
    user = utils.generate_client(app, ("nopassword@example.org", ""))
    assert user.get("/api/v1/identity").status_code == 401
