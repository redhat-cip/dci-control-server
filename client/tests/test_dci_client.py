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

import os

import client.dci_client as dciclient


class TestClient(testtools.TestCase):
    def setUp(self):
        super(TestClient, self).setUp()
        self.print_call = []
        os.environ["DCI_LOGIN"] = 'test_login'
        os.environ["DCI_PASSWORD"] = 'test_password'

    def _catch_print_call(self, a):
        self.print_call.append(str(a))

    def test_main_list(self):
        response = mock.Mock()
        response.json.return_value = {'_items': [
            {'id': 'id', 'name': 'name',
             'created_at': 'created_at', 'updated_at': 'updated_at'}]}
        session = mock.Mock()
        session.get.return_value = response
        with mock.patch.object(dciclient.client.requests, 'Session',
                               return_value=session):
            setattr(dciclient, 'print', self._catch_print_call)
            dciclient.main(args=['list', '--remotecis'])
            self.assertEqual([
                "args: ['list', '--remotecis']",
                '+------------+------+------------+------------+\n'
                '| identifier | name | created_at | updated_at |\n'
                '+------------+------+------------+------------+\n'
                '|     id     | name | created_at | updated_at |\n'
                '+------------+------+------------+------------+'],
                self.print_call)
