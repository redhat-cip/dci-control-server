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


class TestApp(server.tests.DCITestCase):

    def test_post_component_item(self):
        component = self._create_component("admin")
        self.assertEqual(component.status_code, 201)
        component = self._extract_response(component)
        self.component_id = component['id']

    def test_post_test_item(self):
        rv = self._create_test("admin")
        self.assertEqual(rv.status_code, 201)
        response = self._extract_response(rv)
        self.assertIsNotNone(response)

    def test_post_jobdefinition_item(self):
        test = self._create_test("admin")
        self.test_id = self._extract_response(test)['id']
        self.test_post_component_item()
        jobdefinition = self._create_jobdefinition("admin", self.test_id)
        self.jobdefinition_id = self._extract_response(jobdefinition)['id']
        jobdefinition_component = self._create_jobdefinition_component(
            "admin", self.jobdefinition_id, self.component_id)
        self.assertEqual(jobdefinition_component.status_code, 201)
        self.assertIsNotNone(self._extract_response(jobdefinition_component))

    def test_post_remoteci_item(self):
        test = self._create_test("admin")
        test_id = self._extract_response(test)['id']

        remoteci = self._create_remoteci("admin", test_id)
        self.assertEqual(remoteci.status_code, 201)
        response = self._extract_response(remoteci)
        self.assertIsNotNone(response)

    def test_post_job_item_with_no_testversion_id(self):
        """testversion_id is missing, the server should pick a
        testversion that match the test_id of the remoteci.
        """
        self.test_post_jobdefinition_item()
        remoteci = self._create_remoteci("admin", self.test_id)
        remoteci_id = self._extract_response(remoteci)['id']

        job = self._create_job("admin", remoteci_id)
        self.assertEqual(job.status_code, 201)
        response = self._extract_response(job)
        self.assertIsNotNone(response)

    def test_get_job_item(self):
        """GET /jobs should retrieve the item and feed the
        data key with the data section from the component, remoteci,
        test and version.
        """
        self.test_post_jobdefinition_item()
        remoteci = self._create_remoteci("admin", self.test_id)
        remoteci_id = self._extract_response(remoteci)['id']

        job = self._create_job("admin", remoteci_id)
        job_id = self._extract_response(job)['id']

        rv = self.partner_client('get', '/api/jobs/%s' % job_id)
        self.assertEqual(rv.status_code, 200)
        response = self._extract_response(rv)
        self.assertEqual({'component_keys': {'foo': ['bar1', 'bar2']},
                          'remoteci_keys': {'foo': ['bar1', 'bar2']},
                          'test_keys': {'foo': ['bar1', 'bar2']}},
                         response['data'])

    def test_job_recheck(self):
        self.test_post_jobdefinition_item()
        remoteci = self._create_remoteci("admin", self.test_id)
        remoteci_id = self._extract_response(remoteci)['id']

        job = self._create_job("admin", remoteci_id)
        job_id = self._extract_response(job)['id']

        recheck_job = self._create_job("admin", remoteci_id, True, job_id)
        recheck_job_id = self._extract_response(recheck_job)['id']

        rv = self.partner_client('get', '/api/jobs/%s' % recheck_job_id)
        self.assertEqual(rv.status_code, 200)
        response = self._extract_response(rv)

        assert response == 'lol'
