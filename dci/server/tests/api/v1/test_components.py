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

import uuid

import pytest


@pytest.fixture
def pct_id(admin):
    pct = admin.post('/api/v1/componenttypes',
                     data={'name': 'pname'}).data
    return pct['componenttype']['id']


def test_create_components(admin, pct_id):
    pc = admin.post('/api/v1/components',
                    data={'name': 'pname', 'componenttype_id': pct_id}).data
    pc_id = pc['component']['id']
    gc = admin.get('/api/v1/components/%s' % pc_id).data
    assert gc['component']['name'] == 'pname'


# enabled later
def loltest_create_components_already_exist(admin, pct_id):
    pstatus_code = admin.post('/api/v1/components',
                              data={'name': 'pname',
                                    'componenttype_id': pct_id}).status_code
    assert pstatus_code == 201

    pstatus_code = admin.post('/api/v1/components',
                              data={'name': 'pname',
                                    'componenttype_id': pct_id}).status_code
    assert pstatus_code == 400


def test_get_all_components(admin, pct_id):
    created_c_ids = []
    for i in range(5):
        pc = admin.post('/api/v1/components',
                        data={'name': 'pname%s' % uuid.uuid4(),
                              'componenttype_id': pct_id}).data
        created_c_ids.append(pc['component']['id'])
    created_c_ids.sort()

    db_all_cs = admin.get('/api/v1/components').data
    db_all_cs = db_all_cs['components']
    db_all_cs_ids = [db_ct['id'] for db_ct in db_all_cs]
    db_all_cs_ids.sort()

    assert db_all_cs_ids == created_c_ids


def test_get_all_components_with_pagination(admin, pct_id):
    # create 20 component types and check meta data count
    for i in range(20):
        admin.post('/api/v1/components',
                   data={'name': 'pname%s' % uuid.uuid4(),
                         'componenttype_id': pct_id})
    cs = admin.get('/api/v1/components').data
    assert cs['_meta']['count'] == 20

    # verify limit and offset are working well
    for i in range(4):
        cs = admin.get(
            '/api/v1/components?limit=5&offset=%s' % (i * 5)).data
        assert len(cs['components']) == 5

    # if offset is out of bound, the api returns an empty list
    cs = admin.get('/api/v1/components?limit=5&offset=300')
    assert cs.status_code == 200
    assert cs.data['components'] == []


def test_get_all_components_with_embed(admin, pct_id):
    # create 20 component types and check meta data count
    for i in range(10):
        admin.post('/api/v1/components',
                   data={'name': 'pname%s' % uuid.uuid4(),
                         'componenttype_id': pct_id})

    # verify embed
    cs = admin.get('/api/v1/components?embed=componenttype').data

    for component in cs['components']:
        assert 'componenttype_id' not in component
        assert 'componenttype' in component
        assert component['componenttype']['id'] == pct_id


def test_get_component_by_id_or_name(admin, pct_id):
    pc = admin.post('/api/v1/components',
                    data={'name': 'pname', 'componenttype_id': pct_id}).data
    pc_id = pc['component']['id']

    # get by uuid
    created_ct = admin.get('/api/v1/components/%s' % pc_id)
    assert created_ct.status_code == 200

    created_ct = created_ct.data
    assert created_ct['component']['id'] == pc_id

    # get by name
    created_ct = admin.get('/api/v1/components/pname')
    assert created_ct.status_code == 200

    created_ct = created_ct.data
    assert created_ct['component']['id'] == pc_id


def test_get_component_not_found(admin):
    result = admin.get('/api/v1/components/ptdr')
    assert result.status_code == 404


def test_delete_component_by_id(admin, pct_id):
    pc = admin.post('/api/v1/components',
                    data={'name': 'pname', 'componenttype_id': pct_id})
    pct_etag = pc.headers.get("ETag")
    pc_id = pc.data['component']['id']
    assert pc.status_code == 201

    created_ct = admin.get('/api/v1/components/%s' % pc_id)
    assert created_ct.status_code == 200

    deleted_ct = admin.delete('/api/v1/components/%s' % pc_id,
                              headers={'If-match': pct_etag})
    assert deleted_ct.status_code == 204

    gct = admin.get('/api/v1/components/%s' % pc_id)
    assert gct.status_code == 404


def test_delete_component_not_found(admin):
    result = admin.delete('/api/v1/components/ptdr',
                          headers={'If-match': 'mdr'})
    assert result.status_code == 404
