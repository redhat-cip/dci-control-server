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

import os
import random
import subprocess
import sys
import time

import client
import server.tests


class TestClientLib(server.tests.DCITestCase):

    def setUp(self):
        super(TestClientLib, self).setUp()
        environ = os.environ
        environ['OPENSHIFT_POSTGRESQL_DB_URL'] = self.db_uri
        environ['PYTHONPATH'] = '.'
        # NOTE(Gonéri): we should check if the port is available
        port = 5000 + int(random.random() * 1000 % 1000)
        self.server_process = subprocess.Popen([
            sys.executable, './server/app.py', str(port)], env=environ)
        time.sleep(5)
        self.client = client.DCIClient(
            end_point='http://127.0.0.1:%s/api' % port,
            login='admin', password='admin')

    def tearDown(self):
        super(TestClientLib, self).tearDown()
        self.server_process.kill()

    def assertStatusCodeEqual(self, status_code, r):
        print(r.text)
        self.assertEqual(status_code, r.status_code)

    def test_create_delete(self):
        c = self.client

        # write two entries in a row
        self.assertStatusCodeEqual(
            201,
            c.post('/tests', [
                {'name': 'bobby'},
                {'name': 'roberto'}]))

        # get the entry called roberto
        r = c.get('/tests', where={'name': 'roberto'})
        self.assertStatusCodeEqual(
            200,
            r)

        # Overwrite the first entry and compare the result
        initial_item = r.json()['_items'][0]
        self.assertStatusCodeEqual(
            200,
            c.put('/tests/' + initial_item['id'],
                  initial_item['etag'],
                  {'name': 'Jim'}))
        update_item = c.get(
            '/tests',
            where={'name': 'Jim'}).json()['_items'][0]
        self.assertEqual(initial_item['id'], update_item['id'])

        # NOTE(Gonéri): broken with Py27, need to investigate.
        # update the entry and thus produce a new etag
        # self.assertStatusCodeEqual(
        #     200,
        #     c.patch('/tests/' + update_item['id'],
        #             update_item['etag'], {'name': 'Ron'}))
        self.assertStatusCodeEqual(
            200,
            c.put('/tests/' + update_item['id'],
                  update_item['etag'], {'name': 'Ron'}))

        # try to delete the entry with the outdate etag
        self.assertStatusCodeEqual(
            412,
            c.delete('/tests/' + update_item['id'], update_item['etag']))

        # read the new etag
        new_etag = c.get(
            '/tests', where={'name': 'Ron'}).json()['_items'][0]['etag']

        # try to delete the entry with the outdate etag
        self.assertStatusCodeEqual(
            204,
            c.delete('/tests/' + update_item['id'], new_etag))

        # validate there is just 1 entry left
        self.assertEqual(len(c.get('/tests').json()['_items']), 1)

        # drop all the entries from the
        self.assertStatusCodeEqual(
            204,
            c.delete('/tests'))

    def test_find_or_create_or_refresh(self):
        c = self.client

        # First, get the item created
        product = c.find_or_create_or_refresh(
            '/products',
            {'name': 'one product', 'data': {'foo': [1, 2]}})
        self.assertTrue(product['id'])
        old_id = product['id']

        # Then update it
        product = c.find_or_create_or_refresh(
            '/products',
            {'name': 'one product', 'data': {'foo': [1, 2, 3]}})

        # Ensure we preserve the initial item id
        self.assertTrue(product['id'] == old_id)

        # Get the updated product
        product = c.get('/products/' + old_id).json()

        self.assertEqual(product['data']['foo'][2], 3)

        # Finally, try to just find the product
        product = c.find_or_create_or_refresh(
            '/products',
            {'name': 'one product', 'data': {'foo': [1, 2, 3]}})
        self.assertTrue(product['id'] == old_id)

    def test_list_items(self):
        c = self.client

        c.post('/tests', [
            {'name': 'aikido'},
            {'name': 'judo'},
            {'name': 'karate'},
            {'name': 'taekwondobobby'}])

        cpt = 0
        for item in c.list_items('/tests'):
            self.assertTrue(item['name'])
            cpt += 1
        self.assertEqual(cpt, 4)
