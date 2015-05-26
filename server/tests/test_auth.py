# -*- encoding: utf-8 -*-
#
# Copyright 2015 Red Hat, Inc.
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

import mock
import testtools

PW = {
    "admin": "$2a$08$WupvqmmbRXzEj2SvzRldzuz4gbDALWMxk8nQ5xDBa8k0ivb/.TFwu",
    "partner": "$2a$08$ijBXSe7m.epxygjBVCFL/.31nCmX/0/Z39wXovT2PRrzu57MtKsuG"}


class TestClient(testtools.TestCase):

    def setUp(self):
        super(TestClient, self).setUp()
        models = mock.Mock()
        self.m = {
            'eve.flaskapp': mock.Mock(),
            'server.db.models': models,
            'flask': mock.Mock(),
        }
        self.module_patcher = mock.patch.dict('sys.modules', self.m)
        self.module_patcher.start()
        import server.auth
        self.auth_class = server.auth.DCIBasicAuth()

    def tearDown(self):
        super(TestClient, self).tearDown()
        self.module_patcher.stop()

    def set_user_in_db(self, roles, password):
        user_entry = mock.Mock()
        user_entry.password = password
        m_roles = []
        for r in roles:
            m_role = mock.Mock()
            m_role.name = r
            m_roles.append(m_role)
        user_entry.roles = m_roles
        m_qr = mock.Mock()
        m_qr.filter_by.return_value.one.return_value = user_entry
        self.m['server.db.models'].session.query.return_value = m_qr

    def mock_user_input(self, username, password):
        self.m['flask'].request.authorization.password = password
        self.m['flask'].request.authorization.username = username

    def test_authorized_as_partner(self):
        self.set_user_in_db(['partner'], PW['partner'])
        self.mock_user_input('partner', 'partner')
        # partner can create job
        self.assertTrue(self.auth_class.authorized(None, 'jobs', 'POST'))
        # partner cannot create files
        self.assertFalse(self.auth_class.authorized(None, 'files', 'POST'))

    def test_wrong_pw_as_partner(self):
        self.set_user_in_db(['partner'], PW['partner'])
        self.mock_user_input('partner', 'partner')
        self.assertFalse(self.auth_class.authorized(None, 'files', 'POST'))

    def test_authorized_as_admin(self):
        self.set_user_in_db(['admin'], PW['admin'])
        self.mock_user_input('admin', 'admin')
        self.assertTrue(self.auth_class.authorized(None, 'files', 'POST'))

    def test_wrong_pw_as_admin(self):
        self.set_user_in_db(['admin'], PW['admin'])
        self.mock_user_input('admin', 'admin_')
        self.assertFalse(self.auth_class.authorized(None, 'files', 'POST'))
