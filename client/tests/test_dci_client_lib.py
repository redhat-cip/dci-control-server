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
import requests
import subprocess
import sys
import time

import client
import server.tests


def wait_for_http_server(port):
    max_duration = 10
    for i in range(1, max_duration * 10):
        time.sleep(0.1)
        try:
            r = requests.head(
                'http://127.0.0.1:%d/api/componenttypes' % port)
            if r.status_code != 401:
                continue
        except Exception:
            continue
        break
    else:
        print(
            "Failed to start the server in time (%d seconds)." % max_duration)
        sys.exit(1)


class TestClientLib(server.tests.DCITestCase):
    def setUp(self):
        super(TestClientLib, self).setUp()
        environ = os.environ
        environ['OPENSHIFT_POSTGRESQL_DB_URL'] = self.db_uri
        environ['PYTHONPATH'] = '.'
        # NOTE(Gonéri): we should check if the port is available
        port = 5000 + int(random.random() * 1000 % 1000)
        self.server_process = subprocess.Popen(
            [sys.executable, './server/app.py', str(port)],
            env=environ)
        wait_for_http_server(port)
        self.client = client.DCIClient(
            end_point='http://127.0.0.1:%s/api' % port,
            login='admin', password='admin')
        self._componenttype = self.client.post('/componenttypes', {
            'name': 'my_component_type'}).json()

    def tearDown(self):
        super(TestClientLib, self).tearDown()
        self.server_process.kill()

    def assertStatusCodeEqual(self, status_code, r):
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
        self.assertRaises(client.DCIServerError, c.delete,
                          '/tests/' + update_item['id'], update_item['etag'])

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

        component_details = {
            'name': 'one component',
            'componenttype_id': self._componenttype['id'],
            'canonical_project_name': 'this_is_something',
            'data': {'foo': [1, 2]}}

        # First, get the item created
        component = c.find_or_create_or_refresh(
            '/components', component_details)
        self.assertTrue(component['id'])
        old_id = component['id']

        # Then update it
        component_details['data'] = {'foo': [1, 2, 3]}
        component = c.find_or_create_or_refresh(
            '/components',
            component_details)

        # Ensure we preserve the initial item id
        self.assertTrue(component['id'] == old_id)

        # Get the updated component
        component = c.get('/components/' + old_id).json()

        self.assertEqual(component['data']['foo'][2], 3)

        # Finally, try to just find the component
        component = c.find_or_create_or_refresh(
            '/components',
            component_details)
        self.assertTrue(component['id'] == old_id)

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

    def _init_test_call(self):
        c = self.client

        test = self.client.post('/tests', {'name': 'my_test'}).json()
        component = c.post('/components', {
            'name': 'my_component',
            'componenttype_id': self._componenttype['id'],
            'sha': 'some_sha',
            'canonical_project_name': 'my_project'}).json()
        jobdefinition = c.post('/jobdefinitions', {
            'test_id': test['id']}).json()
        c.post('/jobdefinition_components', {
            'jobdefinition_id': jobdefinition['id'],
            'component_id': component['id']}).json()
        team = c.post('/teams', {
            'name': 'my_team'}).json()
        remoteci = c.post('/remotecis', {
            'team_id': team['id'],
            'test_id': test['id']
        }).json()
        job = c.post('/jobs', {
            'team_id': team['id'],
            'jobdefinition_id': jobdefinition['id'],
            'remoteci_id': remoteci['id']}).json()
        self._job_id = job['id']

    def test_call_unicode(self):
        self._init_test_call()
        c = self.client

        r = c.call(self._job_id, ['/bin/echo', 'Café'])
        logfile = c.get(
            '/files',
            where={'jobstate_id': r['jobstate_id']}).json()
        self.assertEqual(
            logfile['_items'][0]['content'],
            u'starting: /bin/echo Café\nCafé\n')

    def test_call_timeout(self):
        self._init_test_call()
        c = self.client

        r = c.call(self._job_id, ['/bin/sleep', '600'], timeout=1)
        logfile = c.get(
            '/files',
            where={'jobstate_id': r['jobstate_id']}).json()
        self.assertEqual(
            logfile['_items'][0]['content'],
            'starting: /bin/sleep 600\n' +
            '1 seconds Timeout! command has been Killed!\n')

    def test_call_cwd(self):
        self._init_test_call()
        c = self.client

        r = c.call(self._job_id, ['/bin/pwd'], cwd='/tmp')
        logfile = c.get(
            '/files',
            where={'jobstate_id': r['jobstate_id']}).json()
        self.assertEqual(
            logfile['_items'][0]['content'],
            u'starting: /bin/pwd\n' +
            '/tmp\n')
        self.assertTrue(r['returncode'] == 0)

    def test_call_failure(self):
        self._init_test_call()
        c = self.client

        r = c.call(self._job_id, ['/bin/ls', '/tmp/no-where-'])
        self.assertTrue(r['returncode'] != 0)
