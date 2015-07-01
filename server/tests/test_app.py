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

    def test_post_product_item(self):
        product = self._create_product()
        self.assertEqual(product.status_code, 201)
        response = self._extract_response(product)
        self.assertIsNotNone(response)

    def test_post_version_item(self):
        product = self._extract_response(self._create_product())
        version = self._create_version(product['id'])
        self.assertEqual(version.status_code, 201)
        response = self._extract_response(version)
        self.assertIsNotNone(response)

    def test_post_test_item(self):
        rv = self._create_test()
        self.assertEqual(rv.status_code, 201)
        response = self._extract_response(rv)
        self.assertIsNotNone(response)

    def test_post_testversion_item(self):
        test = self._create_test()
        test_id = self._extract_response(test)['id']
        product = self._create_product()
        product_id = self._extract_response(product)['id']
        version = self._create_version(product_id)
        version_id = self._extract_response(version)['id']

        testversion = self._create_testversion(test_id, version_id)
        self.assertEqual(testversion.status_code, 201)
        self.assertIsNotNone(self._extract_response(testversion))

    def test_post_remoteci_item(self):
        test = self._create_test()
        test_id = self._extract_response(test)['id']

        remoteci = self._create_remoteci(test_id)
        self.assertEqual(remoteci.status_code, 201)
        response = self._extract_response(remoteci)
        self.assertIsNotNone(response)

    def test_post_job_item_with_no_testversion_id(self):
        """testversion_id is missing, the server should pick a
        testversion that match the test_id of the remoteci.
        """
        test = self._create_test()
        test_id = self._extract_response(test)['id']
        remoteci = self._create_remoteci(test_id)
        remoteci_id = self._extract_response(remoteci)['id']
        product = self._create_product()
        product_id = self._extract_response(product)['id']
        version = self._create_version(product_id)
        version_id = self._extract_response(version)['id']

        self._create_testversion(test_id, version_id)
        job = self._create_job(remoteci_id)
        self.assertEqual(job.status_code, 201)
        response = self._extract_response(job)
        self.assertIsNotNone(response)

    def test_get_job_item(self):
        """GET /jobs should retrieve the item and feed the
        data key with the data section from the product, remoteci,
        test and version.
        """
        test = self._create_test()
        test_id = self._extract_response(test)['id']
        remoteci = self._create_remoteci(test_id)
        remoteci_id = self._extract_response(remoteci)['id']
        product = self._create_product()
        product_id = self._extract_response(product)['id']
        version = self._create_version(product_id)
        version_id = self._extract_response(version)['id']
        self._create_testversion(test_id, version_id)
        job = self._create_job(remoteci_id)
        job_id = self._extract_response(job)['id']

        rv = self.partner_client('get', '/api/jobs/%s' % job_id)
        self.assertEqual(rv.status_code, 200)
        response = self._extract_response(rv)
        self.assertEqual({'product_keys': {'foo': ['bar1', 'bar2']},
                          'remoteci_keys': {'foo': ['bar1', 'bar2']},
                          'test_keys': {'foo': ['bar1', 'bar2']},
                          'version_keys': {'foo': ['bar1', 'bar2']}},
                         response['data'])

    def test_get_versions_extra(self):
        # Create a test
        rv = self._create_test()
        test_id = self._extract_response(rv)['id']

        # Create a product
        rv = self._create_product()
        product_id = self._extract_response(rv)['id']

        # Create a version
        rv = self._create_version(product_id)
        version_id = self._extract_response(rv)['id']

        # Create a testversion
        self._create_testversion(test_id, version_id)

        # Get versions, should be empty
        rv = self.admin_client('get', '/api/versions?extra_data=1')
        self.assertEqual([], self._extract_response(rv)["_items"])
