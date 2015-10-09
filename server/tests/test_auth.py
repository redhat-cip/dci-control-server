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

import server.tests


class TestAuth(server.tests.DCITestCase):

    def test_authorized_as_partner(self):
        # partner can read files
        self.assertHTTPCode(
            self.client_call(
                'get', 'partner', 'partner', '/api/files'), 200)
        # partner can create job (400 because of the missing parameters)
        self.assertHTTPCode(
            self.client_call(
                'post', 'partner', 'partner', '/api/jobs'), 400)

    def test_wrong_pw_as_unauthorized(self):
        self.assertHTTPCode(
            self.client_call('get', 'bob', 'bob', '/api/files'), 401)
        self.assertHTTPCode(
            self.client_call('get', 'bob', 'bob', '/api/jobs'), 401)

    def test_authorized_as_admin(self):
        self.assertHTTPCode(self.client_call(
            'get', 'admin', 'admin', '/api/jobs'), 200)
