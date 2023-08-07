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
from tests.utils import generate_client
import flask
import mock
import pytest


@mock.patch("jwt.api_jwt.datetime", spec=datetime.datetime)
def test_sso_auth_verified(
    m_datetime,
    admin,
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
    nb_users = len(admin.get("/api/v1/users").data["users"])
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
        nb_users_after_sso = len(admin.get("/api/v1/users").data["users"])
        assert (nb_users + 1) == nb_users_after_sso


@mock.patch("jwt.api_jwt.datetime", spec=datetime.datetime)
@mock.patch("dci.auth_mechanism.sso.get_latest_public_key")
def test_sso_auth_verified_public_key_rotation(
    m_get_last_pubkey, m_datetime, user_sso, app, session, team_admin_id
):
    sso_public_key = dci_config.CONFIG["SSO_PUBLIC_KEY"]
    dci_config.CONFIG["SSO_PUBLIC_KEY"] = "= non valid sso public key here ="
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime.fromtimestamp(
        1518653629
    ).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    m_get_last_pubkey.return_value = sso_public_key
    with app.app_context():
        flask.g.team_admin_id = team_admin_id
        flask.g.session = session
        teams = user_sso.get("/api/v1/users/me")
        assert teams.status_code == 200
    assert dci_config.CONFIG["SSO_PUBLIC_KEY"] == sso_public_key


@mock.patch("jwt.api_jwt.datetime", spec=datetime.datetime)
def test_sso_auth_verified_rh_employee(
    m_datetime,
    admin,
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
    nb_users = len(admin.get("/api/v1/users").data["users"])
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
        nb_users_after_sso = len(admin.get("/api/v1/users").data["users"])
        assert (nb_users + 1) == nb_users_after_sso
        # users from redhat team
        redhat_users = admin.get("/api/v1/teams/%s/users" % team_redhat_id).data[
            "users"
        ]
        ro_user_found = False
        for iu in redhat_users:
            if iu["name"] == "dci-rh" and iu["email"] == "dci-rh@redhat.com":
                ro_user_found = True
        assert ro_user_found


@mock.patch("jwt.api_jwt.datetime", spec=datetime.datetime)
def test_sso_auth_update_email_employee_with_preferred_username(
    m_datetime,
    app,
    admin,
):
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime.fromtimestamp(
        1518653629
    ).timetuple()
    m_datetime.utcnow.return_value = m_utcnow

    with app.app_context():
        token_jdoe_with_example_org_email = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InVReHNRcHBzS29vYkZoM0hOdGt1V29SakZkdTBja3RGLVN5NGVXRTV4eTQifQ.eyJqdGkiOiJkNDg1Y2ViNC00ZDVhLTRiMDctODg4Zi1mOTMzNDg2YWNlMTUiLCJleHAiOjE1MTg2NTM4MjksIm5iZiI6MCwiaWF0IjoxNTE4NjUzNTI5LCJpc3MiOiJodHRwOi8vbG9jYWxob3N0OjgxODAvYXV0aC9yZWFsbXMvcmVkaGF0LWV4dGVybmFsIiwiYXVkIjoiZGNpIiwic3ViIjoiMzI3MjQ3NGQtYTA4My00ZTM3LTk0MjYtODY3YWE2YTQ2ZWQ2IiwidHlwIjoiQmVhcmVyIiwiYXpwIjoiZGNpIiwiYXV0aF90aW1lIjowLCJzZXNzaW9uX3N0YXRlIjoiYjc3NGQ3ZWEtMmMzMi00NGE3LTkxYTgtMWI3YzhmZjk4NzA2IiwiYWNyIjoiMSIsImFsbG93ZWQtb3JpZ2lucyI6WyJodHRwOi8vbG9jYWxob3N0OjgwMDAiXSwicmVhbG1fYWNjZXNzIjp7InJvbGVzIjpbInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwiZW1haWwiOiJqZG9lQGV4YW1wbGUub3JnIiwidXNlcm5hbWUiOiJqZG9lIn0.h6dwdIO7Kh6W3e7LUgfqqj1_G6lNcz7w6K_L0qqa1frcSHpIzBSujNtXsUliPHMUSDDXyp6sZC_VWw5rNNtFUzpymTFlAhhHvmepDw2itotIqn_yyV2prEygYK0DKEfwenhwqeGdf34h4B9As1Uz8ZAPoIrbxO4y9dMY8fjQtl_thNzE83GTlvFCAt22DWbr_zeVj6wuJ4C49wPE6huRev9s8KOddWWVVORyM1MXwwR_xu5_F9QJtyTJdQceokP5JwfKrni1MZH_tSM1SOAohwnV8RXfnOnjoFftr6lCQilxQiZU9eGAprmMwzUKnC2iAvTap3iWHnWLs0cW30iaYg"
        john_doe_client = generate_client(
            app, access_token=token_jdoe_with_example_org_email
        )
        r = john_doe_client.get("/api/v1/identity")
        assert r.status_code == 200

        jdoe = admin.get("/api/v1/users?where=email:jdoe@example.org").data["users"][0]
        assert jdoe["name"] == "jdoe"
        assert jdoe["sso_username"] == "jdoe"
        assert jdoe["email"] == "jdoe@example.org"

        token_jdoe_with_red_hat_com_email = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InVReHNRcHBzS29vYkZoM0hOdGt1V29SakZkdTBja3RGLVN5NGVXRTV4eTQifQ.eyJqdGkiOiJkNDg1Y2ViNC00ZDVhLTRiMDctODg4Zi1mOTMzNDg2YWNlMTUiLCJleHAiOjE1MTg2NTM4MjksIm5iZiI6MCwiaWF0IjoxNTE4NjUzNTMwLCJpc3MiOiJodHRwOi8vbG9jYWxob3N0OjgxODAvYXV0aC9yZWFsbXMvcmVkaGF0LWV4dGVybmFsIiwiYXVkIjoiZGNpIiwic3ViIjoiMzI3MjQ3NGQtYTA4My00ZTM3LTk0MjYtODY3YWE2YTQ2ZWQ2IiwidHlwIjoiQmVhcmVyIiwiYXpwIjoiZGNpIiwiYXV0aF90aW1lIjowLCJzZXNzaW9uX3N0YXRlIjoiYjc3NGQ3ZWEtMmMzMi00NGE3LTkxYTgtMWI3YzhmZjk4NzA2IiwiYWNyIjoiMSIsImFsbG93ZWQtb3JpZ2lucyI6WyJodHRwOi8vbG9jYWxob3N0OjgwMDAiXSwicmVhbG1fYWNjZXNzIjp7InJvbGVzIjpbInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwiZW1haWwiOiJqZG9lQHJlZGhhdC5jb20iLCJ1c2VybmFtZSI6Impkb2UifQ.A46fkEKTXGFUJI-h3fRFUmxlBtKbqv83TjTiYy47O0pqSyFzrryn6jvU1pwUAlZqKCD0CjsO43wOsSXs8HABO5jl9vx71un2qvh_qD8nn1MVyV0PITaWSJ-UYPw8tfmdfpyyywFEjrkF5cSQIdJSlIaps-v6QYt-YDwLZSzj_8VHHh9fMF5yP2BYZ1BgjReQn-3A5rz9SD1LNuMQQIv9UvPqnd9zkR9U7LTkgyInh8M2B5RWCNLbdfwKn2lZl-IXKFHywp20jYKodSuyXIE_LEOVSQo4MpFfz25ul5VX-SsUCJc2Z0HihBKoJ-8OP2G2KyVy-Vz6pf6jejt2YcFblw"
        john_doe_client = generate_client(
            app, access_token=token_jdoe_with_red_hat_com_email
        )
        r = john_doe_client.get("/api/v1/identity")
        assert r.status_code == 200

        jdoe = admin.get("/api/v1/users?where=email:jdoe@redhat.com").data["users"][0]
        assert jdoe["name"] == "jdoe"
        assert jdoe["sso_username"] == "jdoe"
        assert jdoe["email"] == "jdoe@redhat.com"


@mock.patch("jwt.api_jwt.datetime", spec=datetime.datetime)
def test_sso_auth_not_verified(
    m_datetime, admin, app, session, access_token, team_admin_id
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
    nb_users = len(admin.get("/api/v1/users").data["users"])
    with app.app_context():
        flask.g.team_admin_id = team_admin_id
        flask.g.session = session
        mech = authm.OpenIDCAuth(sso_headers)
        with pytest.raises(dci_exc.DCIException):
            mech.authenticate()
        assert mech.identity is None
        nb_users_after_sso = len(admin.get("/api/v1/users").data["users"])
        assert nb_users == nb_users_after_sso


@mock.patch("jwt.api_jwt.datetime", spec=datetime.datetime)
def test_sso_auth_get_users(m_datetime, user_sso, app, session, team_admin_id):
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime.fromtimestamp(
        1518653629
    ).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    with app.app_context():
        flask.g.team_admin_id = team_admin_id
        flask.g.session = session
        gusers = user_sso.get("/api/v1/users")
        assert gusers.status_code == 401


@mock.patch("jwt.api_jwt.datetime", spec=datetime.datetime)
def test_sso_auth_get_current_user(m_datetime, user_sso, app, session, team_admin_id):
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime.fromtimestamp(
        1518653629
    ).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    with app.app_context():
        flask.g.team_admin_id = team_admin_id
        flask.g.session = session
        request = user_sso.get("/api/v1/users/me?embed=team,remotecis")
        assert request.status_code == 200
