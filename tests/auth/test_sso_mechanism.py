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

import datetime

import dci.auth_mechanism as authm
from dci.common import exceptions as dci_exc
from dci import dci_config
from tests.settings import SSO_PRIVATE_KEY
from tests.utils import generate_client, generate_jwt
import flask
import mock
import pytest


@mock.patch("jwt.api_jwt.datetime", spec=datetime.datetime)
def test_sso_auth_verified(
    m_datetime,
    client_admin,
    app,
    session,
    access_token,
    team_admin_id,
    team_redhat_id,
    team_epm_id,
):
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime.fromtimestamp(
        1518653629
    ).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    sso_headers = mock.Mock
    sso_headers.headers = {"Authorization": "Bearer %s" % access_token}
    nb_users = len(client_admin.get("/api/v1/users").data["users"])
    with app.app_context():
        flask.g.team_admin_id = team_admin_id
        flask.g.team_redhat_id = team_redhat_id
        flask.g.team_epm_id = team_epm_id
        flask.g.session = session
        mech = authm.OpenIDCAuth(sso_headers)
        assert mech.authenticate()
        assert mech.identity.name == "dci"
        assert mech.identity.sso_username == "dci"
        assert mech.identity.email == "dci@distributed-ci.io"
        nb_users_after_sso = len(client_admin.get("/api/v1/users").data["users"])
        assert (nb_users + 1) == nb_users_after_sso


@mock.patch("jwt.api_jwt.datetime", spec=datetime.datetime)
@mock.patch("dci.auth_mechanism.sso.get_public_key_from_token")
def test_sso_auth_verified_public_key_rotation(
    m_get_public_key_from_token,
    m_datetime,
    sso_client_user1,
    app,
    session,
    team_admin_id,
):
    sso_public_key = dci_config.CONFIG["SSO_PUBLIC_KEY"]
    dci_config.CONFIG["SSO_PUBLIC_KEY"] = "= non valid sso public key here ="
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime.fromtimestamp(
        1518653629
    ).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    m_get_public_key_from_token.return_value = sso_public_key
    with app.app_context():
        flask.g.team_admin_id = team_admin_id
        flask.g.session = session
        teams = sso_client_user1.get("/api/v1/users/me")
        assert teams.status_code == 200
    assert dci_config.CONFIG["SSO_PUBLIC_KEY"] == sso_public_key


@mock.patch("jwt.api_jwt.datetime", spec=datetime.datetime)
def test_sso_auth_verified_rh_employee(
    m_datetime,
    client_admin,
    app,
    session,
    access_token_rh_employee,
    team_admin_id,
    team_redhat_id,
    team_epm_id,
):
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime.fromtimestamp(
        1518653629
    ).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    sso_headers = mock.Mock
    sso_headers.headers = {"Authorization": "Bearer %s" % access_token_rh_employee}
    nb_users = len(client_admin.get("/api/v1/users").data["users"])
    with app.app_context():
        flask.g.team_admin_id = team_admin_id
        flask.g.team_redhat_id = team_redhat_id
        flask.g.team_epm_id = team_epm_id
        flask.g.session = session
        mech = authm.OpenIDCAuth(sso_headers)
        assert mech.authenticate()
        assert mech.identity.name == "dci-rh"
        assert mech.identity.sso_username == "dci-rh"
        assert mech.identity.email == "dci-rh@redhat.com"
        nb_users_after_sso = len(client_admin.get("/api/v1/users").data["users"])
        assert (nb_users + 1) == nb_users_after_sso
        # users from redhat team
        redhat_users = client_admin.get("/api/v1/teams/%s/users" % team_redhat_id).data[
            "users"
        ]
        ro_user_found = False
        for iu in redhat_users:
            if iu["name"] == "dci-rh" and iu["email"] == "dci-rh@redhat.com":
                ro_user_found = True
        assert ro_user_found


def test_sso_auth_update_email_employee_with_preferred_username(
    app,
    client_admin,
):
    with app.app_context():
        john_doe_token = generate_jwt(
            {
                "aud": "dci",
                "sub": "f:436a6686-719b-43ab-a01e-5ecd50b0c8fc:jdoe1@example.org",
                "typ": "Bearer",
                "scope": "openid",
                "name": "John Doe",
                "given_name": "John",
                "family_name": "Doe",
                "email": "jdoe@example.org",
                "username": "jdoe1@example.org",
            },
            SSO_PRIVATE_KEY,
        )
        john_doe_client = generate_client(app, access_token=john_doe_token)
        r = john_doe_client.get("/api/v1/identity")
        assert r.status_code == 200
        jdoe = client_admin.get("/api/v1/users?where=email:jdoe@example.org").data[
            "users"
        ][0]
        assert jdoe["email"] == "jdoe@example.org"

        john_doe_token = generate_jwt(
            {
                "aud": "dci",
                "sub": "f:436a6686-719b-43ab-a01e-5ecd50b0c8fc:jdoe1@example.org",
                "typ": "Bearer",
                "scope": "openid",
                "name": "John Doe",
                "given_name": "John",
                "family_name": "Doe",
                "email": "jdoe@redhat.com",
                "username": "jdoe1@example.org",
            },
            SSO_PRIVATE_KEY,
        )
        john_doe_client = generate_client(app, access_token=john_doe_token)
        r = john_doe_client.get("/api/v1/identity")
        assert r.status_code == 200
        jdoe = client_admin.get("/api/v1/users?where=email:jdoe@redhat.com").data[
            "users"
        ][0]
        assert jdoe["email"] == "jdoe@redhat.com"


def test_user_creation_with_an_old_token(app, client_admin):
    with app.app_context():
        john_doe_token = generate_jwt(
            {
                "aud": "dci",
                "sub": "f:436a6686-719b-43ab-a01e-5ecd50b0c8fc:jdoe1@example.org",
                "typ": "Bearer",
                "scope": "openid",
                "name": "John Doe",
                "given_name": "John",
                "family_name": "Doe",
                "email": "jdoe@example.org",
                "username": "jdoe1@example.org",
            },
            SSO_PRIVATE_KEY,
        )
        john_doe_client = generate_client(app, access_token=john_doe_token)
        r = john_doe_client.get("/api/v1/identity")
        assert r.status_code == 200

        jdoe = client_admin.get("/api/v1/users?where=email:jdoe@example.org").data[
            "users"
        ][0]
        assert jdoe["name"] == "jdoe1@example.org"
        assert jdoe["fullname"] == "John Doe"
        assert jdoe["sso_username"] == "jdoe1@example.org"
        assert jdoe["sso_sub"] is None
        assert jdoe["email"] == "jdoe@example.org"


def test_user_creation_with_a_new_token_without_scope_specified(app, client_admin):
    with app.app_context():
        john_doe_token = generate_jwt(
            {
                "aud": ["dci"],
                "sub": "f:436a6686-719b-43ab-a01e-5ecd50b0c8fc:jdoe1@example.org",
                "typ": "Bearer",
                "scope": "openid",
                "name": "John Doe",
                "given_name": "John",
                "family_name": "Doe",
                "email": "jdoe@example.org",
                "username": "jdoe1@example.org",
            },
            SSO_PRIVATE_KEY,
        )
        john_doe_client = generate_client(app, access_token=john_doe_token)
        r = john_doe_client.get("/api/v1/identity")
        assert r.status_code == 200

        jdoe = client_admin.get("/api/v1/users?where=email:jdoe@example.org").data[
            "users"
        ][0]
        assert jdoe["name"] == "jdoe1@example.org"
        assert jdoe["fullname"] == "John Doe"
        assert jdoe["sso_username"] == "jdoe1@example.org"
        assert jdoe["sso_sub"] is None
        assert jdoe["email"] == "jdoe@example.org"


def test_user_creation_with_a_new_token_with_apidci_scope_specified(app, client_admin):
    with app.app_context():
        john_doe_token = generate_jwt(
            {
                "aud": ["api.dci", "dci"],
                "sub": "87654321",
                "typ": "Bearer",
                "scope": "api.dci",
                "email_verified": True,
                "name": "John Doe",
                "preferred_username": "jdoe1@example.org",
                "given_name": "John",
                "family_name": "Doe",
                "email": "jdoe@example.org",
                "username": "jdoe1@example.org",
            },
            SSO_PRIVATE_KEY,
        )
        john_doe_client = generate_client(app, access_token=john_doe_token)
        r = john_doe_client.get("/api/v1/identity")
        assert r.status_code == 200

        jdoe = client_admin.get("/api/v1/users?where=email:jdoe@example.org").data[
            "users"
        ][0]
        assert jdoe["name"] == "jdoe1@example.org"
        assert jdoe["fullname"] == "John Doe"
        assert jdoe["sso_username"] == "jdoe1@example.org"
        assert jdoe["sso_sub"] == "87654321"
        assert jdoe["email"] == "jdoe@example.org"


def test_user_creation_with_a_new_token_with_apidci_scope_specified_but_dci_audience_not_added(
    app, client_admin
):
    with app.app_context():
        john_doe_token = generate_jwt(
            {
                "aud": ["api.dci"],
                "sub": "87654321",
                "typ": "Bearer",
                "scope": "api.dci",
                "email_verified": True,
                "name": "John Doe",
                "preferred_username": "jdoe1@example.org",
                "email": "jdoe@example.org",
                "username": "not_used@example.org",
            },
            SSO_PRIVATE_KEY,
        )
        john_doe_client = generate_client(app, access_token=john_doe_token)
        r = john_doe_client.get("/api/v1/identity")
        assert r.status_code == 200

        jdoe = client_admin.get("/api/v1/users?where=email:jdoe@example.org").data[
            "users"
        ][0]
        assert jdoe["name"] == "jdoe1@example.org"
        assert jdoe["fullname"] == "John Doe"
        assert jdoe["sso_username"] == "jdoe1@example.org"
        assert jdoe["sso_sub"] == "87654321"
        assert jdoe["email"] == "jdoe@example.org"


@mock.patch("jwt.api_jwt.datetime", spec=datetime.datetime)
def test_sso_auth_not_verified(
    m_datetime, client_admin, app, session, access_token, team_admin_id
):
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime.fromtimestamp(
        1518653629
    ).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    # corrupt access_token
    access_token = access_token + "lol"
    sso_headers = mock.Mock
    sso_headers.headers = {"Authorization": "Bearer %s" % access_token}
    nb_users = len(client_admin.get("/api/v1/users").data["users"])
    with app.app_context():
        flask.g.team_admin_id = team_admin_id
        flask.g.session = session
        mech = authm.OpenIDCAuth(sso_headers)
        with pytest.raises(dci_exc.DCIException):
            mech.authenticate()
        assert mech.identity is None
        nb_users_after_sso = len(client_admin.get("/api/v1/users").data["users"])
        assert nb_users == nb_users_after_sso


@mock.patch("jwt.api_jwt.datetime", spec=datetime.datetime)
def test_sso_auth_get_users(m_datetime, sso_client_user1, app, session, team_admin_id):
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime.fromtimestamp(
        1518653629
    ).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    with app.app_context():
        flask.g.team_admin_id = team_admin_id
        flask.g.session = session
        gusers = sso_client_user1.get("/api/v1/users")
        assert gusers.status_code == 401


@mock.patch("jwt.api_jwt.datetime", spec=datetime.datetime)
def test_sso_auth_get_current_user(
    m_datetime, sso_client_user1, app, session, team_admin_id
):
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime.fromtimestamp(
        1518653629
    ).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    with app.app_context():
        flask.g.team_admin_id = team_admin_id
        flask.g.session = session
        request = sso_client_user1.get("/api/v1/users/me?embed=team,remotecis")
        assert request.status_code == 200
