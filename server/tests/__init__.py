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

import base64

import server
import testtools

import server.app as app


class DCITestCase(testtools.TestCase):

    def setUp(self):
        super(DCITestCase, self).setUp()
        self.app = app
        server.app.app.config['TESTING'] = True
        self.test_client = self.app.app.test_client()

    def client_call(self, method, username, password, *argv):
        encoded_basic_auth = base64.b64encode(
            ("%s:%s" % (
                username, password)).encode('ascii')).decode('utf-8')

        headers = {
            'Authorization': 'Basic ' + encoded_basic_auth
        }
        method_func = getattr(self.test_client, method)
        return method_func(*argv, headers=headers)

    def admin_client(self, method, *argv):
        return self.client_call(method, 'admin', 'admin', *argv)

    def partner_client(self, method, *argv):
        return self.client_call(method, 'partner', 'partner', *argv)

    def unauthorized_client(self, method, *argv):
        return self.client_call(method, 'admin', 'bob', *argv)

    def assertHTTPCode(self, result, code):
        return self.assertEqual(result.status_code, code)
