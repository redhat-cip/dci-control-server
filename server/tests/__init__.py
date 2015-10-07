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
import json
import os
import shutil
import subprocess
import tempfile
import time
import uuid

import testtools


def wait_for_process(buff, expected_pattern):
    while True:
        line = buff.readline().decode()
        if line != "":
            print(line)
        if expected_pattern in line:
            print("*** process is ready ***")
            break
        time.sleep(0.01)


class DCITestCase(testtools.TestCase):
    @classmethod
    def setUpClass(cls):
        super(DCITestCase, cls).setUpClass()

        if hasattr(subprocess, 'DEVNULL'):
            DEVNULL = subprocess.DEVNULL
        else:
            DEVNULL = open(os.devnull, 'wb')

        cls._db_dir = tempfile.mkdtemp()
        subprocess.Popen(['initdb', '--no-locale', cls._db_dir],
                         stdout=DEVNULL).wait()

        with open(cls._db_dir + '/postgresql.conf', 'a+') as pg_cfg_f:
            pg_cfg_f.write("client_encoding = utf8\n")
            pg_cfg_f.write("listen_addresses = ''\n")
            pg_cfg_f.write("fsync = off\n")
            pg_cfg_f.write("full_page_writes = off\n")
            pg_cfg_f.write("log_destination = 'stderr'\n")
            pg_cfg_f.write("logging_collector = off\n")
        cls._pg = subprocess.Popen(['postgres', '-F',
                                    '-k', cls._db_dir,
                                    '-D', cls._db_dir],
                                   stderr=subprocess.PIPE)
        wait_for_process(
            cls._pg.stderr, 'database system is ready')
        subprocess.Popen(['psql', '--quiet',
                          '--echo-hidden', '-h', cls._db_dir,
                          '-f', 'db_schema/dci-control-server.sql',
                          'template1'],
                         stdout=subprocess.PIPE).wait()

        # create roles, teams and users for testing
        with open("%s/%s" % (cls._db_dir, "test_setup.sql"), "w") as f:
            f.write(
                "INSERT INTO teams (name) VALUES ('admin');"
                "INSERT INTO teams (name) VALUES ('partner');"
                "INSERT INTO users (name, password, team_id) VALUES ('admin', "
                "crypt('admin', gen_salt('bf', 8)), (SELECT id FROM teams "
                "WHERE name='partner'));"
                "INSERT INTO users (name, password, team_id) values "
                "('partner', "
                "crypt('partner', gen_salt('bf', 8)), (SELECT id FROM teams "
                "WHERE name='partner'));"
                "INSERT INTO roles (name) VALUES ('admin');"
                "INSERT INTO roles (name) VALUES ('partner');"
                "INSERT INTO user_roles (user_id, role_id) VALUES ((SELECT id "
                "from users "
                "WHERE name='admin'), (SELECT id from roles WHERE "
                "name='admin'));"
                "INSERT INTO user_roles (user_id, role_id) VALUES ((SELECT id "
                "from users "
                "WHERE name='admin'), (SELECT id from roles WHERE "
                "name='partner'));"
                "INSERT INTO user_roles (user_id, role_id) VALUES ((SELECT id "
                "from users "
                "WHERE name='partner'), (SELECT id from roles WHERE "
                "name='partner'));")

        subprocess.check_output(['psql', '-h', cls._db_dir, '-f',
                                 "%s/%s" % (cls._db_dir, "test_setup.sql"),
                                 "template1"],
                                stderr=subprocess.STDOUT)

    @classmethod
    def tearDownClass(cls):
        super(DCITestCase, cls).tearDownClass()
        cls._pg.kill()
        time.sleep(2)
        shutil.rmtree(cls._db_dir)

    def setUp(self):
        super(DCITestCase, self).setUp()
        import server.app
        random_string = str(uuid.uuid1().hex)
        subprocess.call(['createdb', '-h', self._db_dir,
                         '-T', 'template1', random_string])
        self.db_uri = "postgresql:///?host=%s&dbname=%s" % (
            self._db_dir, random_string)
        self.app = server.app.create_app(self.db_uri)
        self.app.testing = True
        self.test_client = self.app.test_client()

    def client_call(self, method, username, password, path, **argv):
        encoded_basic_auth = base64.b64encode(
            ("%s:%s" % (
                username, password)).encode('ascii')).decode('utf-8')

        headers = {
            'Authorization': 'Basic ' + encoded_basic_auth,
            'Content-Type': 'application/json'
        }
        method_func = getattr(self.test_client, method)
        if 'data' in argv:
            argv['data'] = json.dumps(argv['data'])
        return method_func(path, headers=headers, **argv)

    def admin_client(self, method, path, **argv):
        return self.client_call(method, 'admin', 'admin', path, **argv)

    def partner_client(self, method, path, **argv):
        return self.client_call(method, 'partner', 'partner', path, **argv)

    def unauthorized_client(self, method, path, **argv):
        return self.client_call(method, 'admin', 'bob', path, **argv)

    def assertHTTPCode(self, result, code):
        return self.assertEqual(result.status_code, code)

    @staticmethod
    def _extract_response(rv):
        return json.loads(rv.get_data().decode())

    def _create_component(self, client):
        client = getattr(self, "%s_client" % client)
        componenttype = self._extract_response(
            client('post', '/api/componenttypes',
                   data={'name': 'a_component_type'}))
        return client(
            'post',
            '/api/components',
            data={'name': 'bob',
                  'canonical_project_name': 'this_is_something',
                  'componenttype_id': componenttype['id'],
                  'data': {
                      'component_keys': {
                          'foo': ['bar1', 'bar2']}}})

    def _create_jobdefinition(self, client, test_id):
        return getattr(self, "%s_client" % client)(
            'post',
            '/api/jobdefinitions',
            data={'name': 'bob',
                  'priority': 0,
                  'test_id': test_id})

    def _create_test(self, client):
        return getattr(self, "%s_client" % client)(
            'post',
            '/api/tests',
            data={
                'name': 'bob',
                'data': {
                    'test_keys': {
                        'foo': ['bar1', 'bar2']}}})

    def _create_jobdefinition_component(
            self, client, jobdefinition_id, component_id):
        return getattr(self, "%s_client" % client)(
            'post',
            '/api/jobdefinition_components',
            data={
                'jobdefinition_id': jobdefinition_id,
                'component_id': component_id})

    def _create_remoteci(self, client, test_id):
        return getattr(self, "%s_client" % client)(
            'post',
            '/api/remotecis',
            data={
                'name': 'a_remoteci',
                'test_id': test_id,
                'data': {
                    'remoteci_keys': {
                        'foo': ['bar1', 'bar2']}}})

    def _create_job(self, client, remoteci_id):
        return getattr(self, "%s_client" % client)(
            'post',
            '/api/jobs',
            data={'remoteci_id': remoteci_id,
                  'recheck': False})
