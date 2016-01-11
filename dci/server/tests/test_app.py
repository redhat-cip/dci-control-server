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

from sample import db_provisioning


def test_cors_preflight(admin):
    headers = {
        'Origin': 'http://foo.example',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Authorization'
    }
    resp = admin.options('/api/v1', headers=headers)
    headers = resp.headers
    assert resp.status_code == 200
    assert headers['Access-Control-Allow-Headers'] == 'Authorization'
    assert headers['Access-Control-Allow-Origin'] == '*'
    assert headers['Access-Control-Allow-Methods'] == 'GET, POST, PUT, DELETE'


def test_cors_headers(admin):
    resp = admin.get('/api/v1/jobs')
    assert resp.headers['Access-Control-Allow-Origin'] == '*'


def test_sample_db_provisionning(engine, db_clean):
    """Test the sample init_db method, to be sure it will
    not be broken when updating
    """

    with engine.begin() as db_conn:
        db_provisioning.init_db(db_conn)
