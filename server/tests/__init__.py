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
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

import testtools


class DCITestCase(testtools.TestCase):
    @classmethod
    def setUpClass(cls):
        super(DCITestCase, cls).setUpClass()
        cls._db_dir = tempfile.mkdtemp()
        subprocess.call(['initdb', '--no-locale', cls._db_dir])
        subprocess.call(['sed', '-i',
                         "s,#listen_addresses.*,listen_addresses = '',",
                         '%s/postgresql.conf' % cls._db_dir])
        cls._pg = subprocess.Popen(['postgres', '-F',
                                    '-k', cls._db_dir,
                                    '-D', cls._db_dir])
        time.sleep(0.5)
        subprocess.call(['psql', '--quiet',
                         '--echo-hidden', '-h', cls._db_dir,
                         '-f', 'db_schema/dci-control-server.sql',
                         'template1'])
        time.sleep(0.3)
        res = subprocess.call(['psql', '-c',
                               "\"INSERT INTO teams (name) VALUES ('admin');\""])
        if res:
            print("error1")
            sys.exit(1)
        res = subprocess.call(['psql', '-c',
                         "\"INSERT INTO roles (name) VALUES ('admin');\""])
        if res:
            print("error2")
            sys.exit(1)

        res = subprocess.call(['psql', '-c',
                         "\"INSERT INTO users (name, password, team_id) "\
                         "VALUES ('admin', crypt('admin', "\
                         "gen_salt('bf', 8)), (SELECT id FROM teams "\
                         "WHERE name='admin'));\""])
        if res:
            print("error3")
            sys.exit(1)
        time.sleep(0.3)

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
        self.app.config['TESTING'] = True
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

    def _create_product(self, client):
        return getattr(self, "%s_client" % client)(
            'post',
            '/api/products',
            data={'name': 'bob',
                  'data': {
                      'product_keys': {
                          'foo': ['bar1', 'bar2']}}})

    def _create_version(self, client, product_id):
        return getattr(self, "%s_client" % client)(
            'post',
            '/api/versions',
            data={'name': 'bob',
                  'product_id': product_id,
                  'data': {
                      'version_keys': {
                          'foo': ['bar1', 'bar2']}}})

    def _create_test(self, client):
        return getattr(self, "%s_client" % client)(
            'post',
            '/api/tests',
            data={
                'name': 'bob',
                'data': {
                    'test_keys': {
                        'foo': ['bar1', 'bar2']}}})

    def _create_testversion(self, client, test_id, version_id):
        return getattr(self, "%s_client" % client)(
            'post',
            '/api/testversions',
            data={
                'test_id': test_id,
                'version_id': version_id})

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
            data={'remoteci_id': remoteci_id})
