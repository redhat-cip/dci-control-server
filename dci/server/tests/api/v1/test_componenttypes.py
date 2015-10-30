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


def test_create_componenttypes(admin):
    pct = admin.post('/api/v1/componenttypes',
                     data={'name': 'pname'}).data
    pct_id = pct['componenttype']['id']
    gct = admin.get('/api/v1/componenttypes/%s' % pct_id).data
    assert gct['componenttype']['name'] == 'pname'


def test_create_componenttypes_already_exist(admin):
    pstatus_code = admin.post('/api/v1/componenttypes',
                              data={'name': 'pname'}).status_code
    assert pstatus_code == 201

    pstatus_code = admin.post('/api/v1/componenttypes',
                              data={'name': 'pname'}).status_code
    assert pstatus_code == 400


def test_get_all_componenttypes(admin):
    created_cts_ids = []
    for i in range(21):
        pct = admin.post('/api/v1/componenttypes',
                         data={'name': 'pname%s' % uuid.uuid4()}).data
        created_cts_ids.append(pct['componenttype']['id'])
    created_cts_ids.sort()

    db_all_cts = admin.get('/api/v1/componenttypes').data
    db_all_cts = db_all_cts['componenttypes']
    db_all_cts_ids = [db_ct['id'] for db_ct in db_all_cts]
    db_all_cts_ids.sort()

    assert db_all_cts_ids == created_cts_ids


def test_get_componenttype_by_id_or_name(admin):
    pct = admin.post('/api/v1/componenttypes',
                     data={'name': 'pname'}).data
    pct_id = pct['componenttype']['id']

    # get by uuid
    created_ct = admin.get('/api/v1/componenttypes/%s' % pct_id)
    assert created_ct.status_code == 200

    created_ct = created_ct.data
    assert created_ct['componenttype']['id'] == pct_id

    # get by name
    created_ct = admin.get('/api/v1/componenttypes/pname')
    assert created_ct.status_code == 200

    created_ct = created_ct.data
    assert created_ct['componenttype']['id'] == pct_id


def test_get_componenttype_not_found(admin):
    result = admin.get('/api/v1/componenttypes/ptdr')
    assert result.status_code == 404


def test_put_componenttypes(admin):
    pct = admin.post('/api/v1/componenttypes', data={'name': 'pname'})
    assert pct.status_code == 201

    pct_etag = pct.headers.get("ETag")

    gct = admin.get('/api/v1/componenttypes/pname')
    assert gct.status_code == 200

    ppct = admin.put('/api/v1/componenttypes/pname',
                     data={'name': 'nname'},
                     headers={'If-match': pct_etag})
    assert ppct.status_code == 204

    gct = admin.get('/api/v1/componenttypes/pname')
    assert gct.status_code == 404

    gct = admin.get('/api/v1/componenttypes/nname')
    assert gct.status_code == 200


def test_delete_componenttype_by_id(admin):
    pct = admin.post('/api/v1/componenttypes',
                     data={'name': 'pname'})
    pct_etag = pct.headers.get("ETag")
    pct_id = pct.data['componenttype']['id']
    assert pct.status_code == 201

    created_ct = admin.get('/api/v1/componenttypes/%s' % pct_id)
    assert created_ct.status_code == 200

    deleted_ct = admin.delete('/api/v1/componenttypes/%s' % pct_id,
                              headers={'If-match': pct_etag})
    assert deleted_ct.status_code == 204

    gct = admin.get('/api/v1/componenttypes/%s' % pct_id)
    assert gct.status_code == 404


def test_delete_componenttype_not_found(admin):
    result = admin.delete('/api/v1/componenttypes/ptdr',
                          headers={'If-match': 'mdr'})
    assert result.status_code == 404
