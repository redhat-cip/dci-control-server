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


def test_create_tests(admin):
    pct = admin.post('/api/v1/tests',
                     data={'name': 'pname'}).data
    pct_id = pct['test']['id']
    gct = admin.get('/api/v1/tests/%s' % pct_id).data
    assert gct['test']['name'] == 'pname'


# TODO(yassine): activated later
def loltest_create_tests_already_exist(admin):
    pstatus_code = admin.post('/api/v1/tests',
                              data={'name': 'pname'}).status_code
    assert pstatus_code == 201

    pstatus_code = admin.post('/api/v1/tests',
                              data={'name': 'pname'}).status_code
    assert pstatus_code == 400


def test_get_all_tests(admin):
    created_cts_ids = []
    for i in range(5):
        pct = admin.post('/api/v1/tests',
                         data={'name': 'pname%s' % uuid.uuid4()}).data
        created_cts_ids.append(pct['test']['id'])
    created_cts_ids.sort()

    db_all_cts = admin.get('/api/v1/tests').data
    db_all_cts = db_all_cts['tests']
    db_all_cts_ids = [db_ct['id'] for db_ct in db_all_cts]
    db_all_cts_ids.sort()

    assert db_all_cts_ids == created_cts_ids


def test_get_all_tests_with_where(admin):
    ct = admin.post('/api/v1/tests',
                    data={'name': 'pname1'}).data
    ct_id = ct['test']['id']

    db_ct = admin.get('/api/v1/tests?where=id:%s'
                      % ct_id).data
    db_ct_id = db_ct['tests'][0]['id']
    assert db_ct_id == ct_id

    db_ct = admin.get('/api/v1/tests?where=name:pname1').data
    db_ct_id = db_ct['tests'][0]['id']
    assert db_ct_id == ct_id


def test_get_all_tests_with_pagination(admin):
    # create 20 component types and check meta data count
    for i in range(20):
        admin.post('/api/v1/tests',
                   data={'name': 'pname%s' % uuid.uuid4()})
    cts = admin.get('/api/v1/tests').data
    assert cts['_meta']['count'] == 20

    # verifiy limit and offset are working well
    for i in range(4):
        cts = admin.get(
            '/api/v1/tests?limit=5&offset=%s' % (i * 5)).data
        assert len(cts['tests']) == 5

    # if offset is out of bound, the api returns an empty list
    cts = admin.get('/api/v1/tests?limit=5&offset=300')
    assert cts.status_code == 200
    assert cts.data['tests'] == []


def test_get_all_tests_with_sort(admin):
    # create 3 components types ordered by created time
    ct_1 = admin.post('/api/v1/tests',
                      data={'name': 'pname1'}).data['test']
    ct_2 = admin.post('/api/v1/tests',
                      data={'name': 'pname2'}).data['test']
    ct_3 = admin.post('/api/v1/tests',
                      data={'name': 'pname3'}).data['test']

    cts = admin.get('/api/v1/tests?sort=created_at').data
    assert cts['tests'] == [ct_1, ct_2, ct_3]

    # test in reverse order
    cts = admin.get('/api/v1/tests?sort=-created_at').data
    assert cts['tests'] == [ct_3, ct_2, ct_1]


def test_get_test_by_id_or_name(admin):
    pct = admin.post('/api/v1/tests',
                     data={'name': 'pname'}).data
    pct_id = pct['test']['id']

    # get by uuid
    created_ct = admin.get('/api/v1/tests/%s' % pct_id)
    assert created_ct.status_code == 200

    created_ct = created_ct.data
    assert created_ct['test']['id'] == pct_id

    # get by name
    created_ct = admin.get('/api/v1/tests/pname')
    assert created_ct.status_code == 200

    created_ct = created_ct.data
    assert created_ct['test']['id'] == pct_id


def test_get_test_not_found(admin):
    result = admin.get('/api/v1/tests/ptdr')
    assert result.status_code == 404


def test_put_tests(admin):
    pct = admin.post('/api/v1/tests', data={'name': 'pname'})
    assert pct.status_code == 201

    pct_etag = pct.headers.get("ETag")

    gct = admin.get('/api/v1/tests/pname')
    assert gct.status_code == 200

    ppct = admin.put('/api/v1/tests/pname',
                     data={'name': 'nname'},
                     headers={'If-match': pct_etag})
    assert ppct.status_code == 204

    gct = admin.get('/api/v1/tests/pname')
    assert gct.status_code == 404

    gct = admin.get('/api/v1/tests/nname')
    assert gct.status_code == 200


def test_delete_test_by_id(admin):
    pct = admin.post('/api/v1/tests',
                     data={'name': 'pname'})
    pct_etag = pct.headers.get("ETag")
    pct_id = pct.data['test']['id']
    assert pct.status_code == 201

    created_ct = admin.get('/api/v1/tests/%s' % pct_id)
    assert created_ct.status_code == 200

    deleted_ct = admin.delete('/api/v1/tests/%s' % pct_id,
                              headers={'If-match': pct_etag})
    assert deleted_ct.status_code == 204

    gct = admin.get('/api/v1/tests/%s' % pct_id)
    assert gct.status_code == 404


def test_delete_test_not_found(admin):
    result = admin.delete('/api/v1/tests/ptdr',
                          headers={'If-match': 'mdr'})
    assert result.status_code == 404
