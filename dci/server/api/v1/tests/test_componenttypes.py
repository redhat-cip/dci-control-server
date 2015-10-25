# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Red Hat, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from flask import json

import uuid


def test_create_componenttypes(test_client):
    pct = test_client.post('/api/v1/componenttypes',
                           data={'name': 'pname'}).data
    pct_id = json.loads(pct)['componenttype']['id']
    gct = test_client.get('/api/v1/componenttypes/%s' % pct_id).data
    gct = json.loads(gct)
    assert gct['componenttype']['name'] == 'pname'


# This test will be activated later
def loltest_create_componenttypes_already_exist(test_client):
    pstatus_code = test_client.post('/api/v1/componenttypes',
                                    data={'name': 'pname'}).status_code
    assert pstatus_code == 201

    pstatus_code = test_client.post('/api/v1/componenttypes',
                                    data={'name': 'pname'}).status_code
    assert pstatus_code == 422


def test_get_all_componenttypes(test_client):
    created_cts_ids = []
    for i in range(21):
        pct = test_client.post('/api/v1/componenttypes',
                               data={'name': 'pname%s' % uuid.uuid4()}).data
        pct = json.loads(pct)
        created_cts_ids.append(pct['id'])
    created_cts_ids.sort()

    db_all_cts = test_client.get('/api/v1/componenttypes').data
    db_all_cts = json.loads(db_all_cts)['componenttypes']
    db_all_cts_ids = [db_ct['id'] for db_ct in db_all_cts]
    db_all_cts_ids.sort()

    assert db_all_cts_ids == created_cts_ids


# This test fails because of comparison between string and PG UUID
def loltest_get_componenttype_by_id_or_name(test_client):
    pct = test_client.post('/api/v1/componenttypes',
                           data={'name': 'pname'}).data
    pct = json.loads(pct)

    created_ct = test_client.get('/api/v1/componenttypes/%s' % pct['id'])
    assert created_ct.status_code == 200
    created_ct = json.loads(created_ct.data)

    assert created_ct['id'] == pct['id']

    # 'pname' could not be compared with PG UUID
    created_ct = test_client.get('/api/v1/componenttypes/pname')
    assert created_ct.status_code == 200
    created_ct = json.loads(created_ct.data)

    assert created_ct['id'] == pct['id']


def loltest_get_componenttype_by_id_or_name_not_found(test_client):
    pass


def test_delete_componenttype_by_id(test_client):
    pct = test_client.post('/api/v1/componenttypes',
                           data={'name': 'pname'})
    pct_id = json.loads(pct.data)['id']
    assert pct.status_code == 201

    created_ct = test_client.get('/api/v1/componenttypes/%s' % pct_id)
    assert created_ct.status_code == 200

    deleted_ct = test_client.delete('/api/v1/componenttypes/%s' % pct_id)
    assert deleted_ct.status_code == 204

    gct = test_client.get('/api/v1/componenttypes/%s' % pct_id)
    assert gct.status_code == 404
