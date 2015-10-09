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

import client as dci_client
import client.tests.utils as utils
import pytest


class TestClientLib(object):

    def test_create_delete(self, client):
        # write two entries in a row
        tests = client.post('/tests', [
            {'name': 'bobby'},
            {'name': 'roberto'}
        ])

        assert tests.status_code == 201

        # get the entry called roberto
        roberto = client.get('/tests', where={'name': 'roberto'})
        assert roberto.status_code == 200

        # Overwrite the first entry and compare the result
        roberto = roberto.json()['_items'][0]

        jim = client.put('/tests/%s' % roberto['id'],
                         roberto['etag'],
                         {'name': 'Jim'})

        assert jim.status_code == 200
        jim = client.get('/tests', where={'name': 'Jim'})

        jim = jim.json()['_items'][0]

        assert jim['id'] == roberto['id']

        # NOTE(Gonéri): broken with Py27, need to investigate.
        # update the entry and thus produce a new etag
        # self.assertStatusCodeEqual(
        #     200,
        #     c.patch('/tests/' + update_item['id'],
        #             update_item['etag'], {'name': 'Ron'}))

        ron = client.put('/tests/%s' % jim['id'],
                         jim['etag'],
                         {'name': 'Ron'})

        assert ron.status_code == 200
        # try to delete the entry with the outdate etag
        with pytest.raises(dci_client.DCIServerError):
            client.delete('/tests/%s' % jim['id'], jim['etag'])

        # read the new etag
        new_etag = (client
                    .get('/tests', where={'name': 'Ron'})
                    .json()['_items'][0]['etag'])

        # try to delete the entry with the outdate etag
        delete = client.delete('/tests/%s' % jim['id'], new_etag)

        assert delete.status_code == 204
        # validate there is just 1 entry left
        items_left = client.get('/tests').json()['_items']
        assert len(items_left) == 1

        # drop all the entries
        delete = client.delete('/tests')
        assert delete.status_code == 204

    def test_find_or_create_or_refresh(self, client):
        componenttype = utils.generate_componenttype(client)
        component_details = {
            'name': 'one component',
            'componenttype_id': componenttype['id'],
            'canonical_project_name': 'this_is_something',
            'data': {'foo': [1, 2]}
        }

        # First, get the item created
        component = client.find_or_create_or_refresh(
            '/components', component_details
        )
        assert component['id'] is not None

        old_id = component['id']

        # Then update it
        component_details['data'] = {'foo': [1, 2, 3]}
        component = client.find_or_create_or_refresh(
            '/components', component_details
        )

        # Ensure we preserve the initial item id
        assert component['id'] == old_id

        # Get the updated component
        component = client.get('/components/%s' % old_id).json()

        assert component['data']['foo'][2] == 3

        # Finally, try to just find the component
        component = client.find_or_create_or_refresh(
            '/components', component_details
        )
        assert component['id'] == old_id

    def test_list_items(self, client):

        client.post('/tests', [{'name': 'aikido'},
                               {'name': 'judo'},
                               {'name': 'karate'},
                               {'name': 'taekwondobobby'}])

        items = list(client.list_items('/tests'))
        for item in items:
            assert item['name'] is not None
        assert len(items) == 4

    def test_call_unicode(self, client):
        job = utils.generate_job(client)

        r = client.call(job['id'], ['/bin/echo', 'Café'])

        logfile = client.get(
            '/files', where={'jobstate_id': r['jobstate_id']}
        ).json()

        logfile['_items'][0]['content'] == u'starting: /bin/echo Café\nCafé\n'

    def test_call_timeout(self, client):
        job = utils.generate_job(client)

        r = client.call(job['id'], ['/bin/sleep', '600'], timeout=1)
        logfile = client.get(
            '/files', where={'jobstate_id': r['jobstate_id']}
        ).json()

        assert logfile['_items'][0]['content'] == (
            'starting: /bin/sleep 600\n'
            '1 seconds Timeout! command has been Killed!\n'
        )

    def test_call_cwd(self, client):
        job = utils.generate_job(client)

        r = client.call(job['id'], ['/bin/pwd'], cwd='/tmp')
        logfile = client.get(
            '/files', where={'jobstate_id': r['jobstate_id']}
        ).json()

        assert logfile['_items'][0]['content'] == (
            u'starting: /bin/pwd\n/tmp\n'
        )
        assert r['returncode'] == 0

    def test_call_failure(self, client):
        job = utils.generate_job(client)

        r = client.call(job['id'], ['/bin/ls', '/tmp/no-where-'])
        assert r['returncode'] != 0
