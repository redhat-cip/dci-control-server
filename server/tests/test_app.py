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

import server.app
import server.db.models
import server.tests


class TestApp_resource_creation(server.tests.DCITestCase):

    def test_post_component_item(self):
        r = self._create_component("admin")
        self.assertHTTPCode(r, 201)
        self.component_id = r.json()['id']

    def test_post_test_item(self):
        r = self._create_test("admin")
        self.assertHTTPCode(r, 201)
        self.assertIsNotNone(r.json())

    def test_post_remoteci_item(self):
        r = self._create_test("admin")
        test_id = r.json()['id']
        r = self._create_remoteci("admin", test_id)
        self.assertHTTPCode(r, 201)
        self.assertIsNotNone(r.json())


class TestApp_handle_job(server.tests.DCITestCase):

    def setUp(self):
        super(TestApp_handle_job, self).setUp()
        r = self._create_test("admin")
        self.test_id = r.json()['id']
        r = self._create_component("admin")
        self.component_id = r.json()['id']
        r = self._create_jobdefinition("admin", self.test_id)
        self.jobdefinition_id = r.json()['id']
        r = self._create_jobdefinition_component(
            "admin", self.jobdefinition_id, self.component_id)

    def test_post_job_item_with_no_testversion_id(self):
        """testversion_id is missing, the server should pick a
        testversion that match the test_id of the remoteci.
        """
        r = self._create_remoteci("admin", self.test_id)
        remoteci_id = r.json()['id']

        r = self._create_job("admin", remoteci_id)
        self.assertHTTPCode(r, 201)
        self.assertIsNotNone(r.json())

    def test_get_job_item(self):
        """GET /jobs should retrieve the item and feed the
        data key with the data section from the component, remoteci,
        test and version.
        """
        r = self._create_remoteci("admin", self.test_id)
        remoteci_id = r.json()['id']

        r = self._create_job("admin", remoteci_id)
        job_id = r.json()['id']

        r = self.client_call(
            'get',
            'partner',
            'partner',
            '/api/jobs/%s' % job_id)
        self.assertHTTPCode(r, 200)
        self.assertEqual({'component_keys': {'foo': ['bar1', 'bar2']},
                          'remoteci_keys': {'foo': ['bar1', 'bar2']},
                          'test_keys': {'foo': ['bar1', 'bar2']}},
                         r.json()['data'])
