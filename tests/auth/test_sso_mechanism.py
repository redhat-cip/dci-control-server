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

import flask
import mock
import pytest


@mock.patch('jwt.api_jwt.datetime', spec=datetime.datetime)
def test_sso_auth_verified(m_datetime, admin, app, engine, access_token,
                           team_admin_id, team_redhat_id, team_epm_id):
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime. \
        fromtimestamp(1518653629).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    sso_headers = mock.Mock
    sso_headers.headers = {'Authorization': 'Bearer %s' % access_token}
    nb_users = len(admin.get('/api/v1/users').data['users'])
    with app.app_context():
        flask.g.team_admin_id = team_admin_id
        flask.g.team_redhat_id = team_redhat_id
        flask.g.team_epm_id = team_epm_id
        flask.g.db_conn = engine.connect()
        mech = authm.OpenIDCAuth(sso_headers)
        assert mech.authenticate()
        assert mech.identity.name == 'dci'
        assert mech.identity.sso_username == 'dci'
        assert mech.identity.email == 'dci@distributed-ci.io'
        nb_users_after_sso = len(admin.get('/api/v1/users').data['users'])
        assert (nb_users + 1) == nb_users_after_sso


@mock.patch('jwt.api_jwt.datetime', spec=datetime.datetime)
@mock.patch('dci.auth_mechanism.utils.get_latest_public_key')
def test_sso_auth_verified_public_key_rotation(m_get_last_pubkey, m_datetime,
                                               user_sso, app, engine,
                                               team_admin_id):
    sso_public_key = dci_config.CONFIG['SSO_PUBLIC_KEY']
    dci_config.CONFIG['SSO_PUBLIC_KEY'] = '= non valid sso public key here ='
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime. \
        fromtimestamp(1518653629).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    m_get_last_pubkey.return_value = sso_public_key
    with app.app_context():
        flask.g.team_admin_id = team_admin_id
        flask.g.db_conn = engine.connect()
        teams = user_sso.get('/api/v1/users/me')
        assert teams.status_code == 200
    assert dci_config.CONFIG['SSO_PUBLIC_KEY'] == sso_public_key


@mock.patch('jwt.api_jwt.datetime', spec=datetime.datetime)
def test_sso_auth_verified_rh_employee(m_datetime, admin, app, engine, access_token_rh_employee,  # noqa
                                       team_admin_id, team_redhat_id, team_epm_id):  # noqa
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime. \
        fromtimestamp(1518653629).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    sso_headers = mock.Mock
    sso_headers.headers = {'Authorization': 'Bearer %s' % access_token_rh_employee}
    nb_users = len(admin.get('/api/v1/users').data['users'])
    with app.app_context():
        flask.g.team_admin_id = team_admin_id
        flask.g.team_redhat_id = team_redhat_id
        flask.g.team_epm_id = team_epm_id
        flask.g.db_conn = engine.connect()
        mech = authm.OpenIDCAuth(sso_headers)
        assert mech.authenticate()
        assert mech.identity.name == 'dci-rh'
        assert mech.identity.sso_username == 'dci-rh'
        assert mech.identity.email == 'dci-rh@redhat.com'
        nb_users_after_sso = len(admin.get('/api/v1/users').data['users'])
        assert (nb_users + 1) == nb_users_after_sso
        # users from redhat team
        redhat_users = admin.get('/api/v1/teams/%s/users' % team_redhat_id).data['users']  # noqa
        ro_user_found = False
        print('t1 %s' % team_redhat_id)
        for iu in redhat_users:
            if iu['name'] == 'dci-rh' and iu['email'] == 'dci-rh@redhat.com':
                ro_user_found = True
        assert ro_user_found


@mock.patch('jwt.api_jwt.datetime', spec=datetime.datetime)
def test_sso_auth_not_verified(m_datetime, admin, app, engine, access_token,
                               team_admin_id):
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime. \
        fromtimestamp(1518653629).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    # corrupt access_token
    access_token = access_token + 'lol'
    sso_headers = mock.Mock
    sso_headers.headers = {'Authorization': 'Bearer %s' % access_token}
    nb_users = len(admin.get('/api/v1/users').data['users'])
    with app.app_context():
        flask.g.team_admin_id = team_admin_id
        flask.g.db_conn = engine.connect()
        mech = authm.OpenIDCAuth(sso_headers)
        with pytest.raises(dci_exc.DCIException):
            mech.authenticate()
        assert mech.identity is None
        nb_users_after_sso = len(admin.get('/api/v1/users').data['users'])
        assert nb_users == nb_users_after_sso


@mock.patch('jwt.api_jwt.datetime', spec=datetime.datetime)
def test_sso_auth_get_users(m_datetime, user_sso, app, engine, team_admin_id):
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime. \
        fromtimestamp(1518653629).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    with app.app_context():
        flask.g.team_admin_id = team_admin_id
        flask.g.db_conn = engine.connect()
        gusers = user_sso.get('/api/v1/users')
        assert gusers.status_code == 200


@mock.patch('jwt.api_jwt.datetime', spec=datetime.datetime)
def test_sso_auth_get_current_user(m_datetime, user_sso, app, engine,
                                   team_admin_id):
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime. \
        fromtimestamp(1518653629).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    with app.app_context():
        flask.g.team_admin_id = team_admin_id
        flask.g.db_conn = engine.connect()
        request = user_sso.get('/api/v1/users/me?embed=team,remotecis')
        assert request.status_code == 200
