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


def test_create_tests(admin):
    pt = admin.post('/api/v1/tests',
                    data={'name': 'pname'}).data
    pt_id = pt['test']['id']
    gt = admin.get('/api/v1/tests/%s' % pt_id).data
    assert gt['test']['name'] == 'pname'


# TODO(yassine): activated later
# because the unique integrity constraint on name is missing so far
def loltest_create_tests_already_exist(admin):
    pstatus_code = admin.post('/api/v1/tests',
                              data={'name': 'pname'}).status_code
    assert pstatus_code == 201

    pstatus_code = admin.post('/api/v1/tests',
                              data={'name': 'pname'}).status_code
    assert pstatus_code == 400


def test_get_all_tests(admin):
    test_1 = admin.post('/api/v1/tests', data={'name': 'pname1'}).data
    test_2 = admin.post('/api/v1/tests', data={'name': 'pname2'}).data

    db_all_tests = admin.get('/api/v1/tests?sort=created_at').data
    db_all_tests = db_all_tests['tests']
    db_all_tests_ids = [db_t['id'] for db_t in db_all_tests]

    assert db_all_tests_ids == [test_1['test']['id'], test_2['test']['id']]


def test_get_all_tests_with_where(admin):
    pt = admin.post('/api/v1/tests', data={'name': 'pname1'}).data
    pt_id = pt['test']['id']

    db_t = admin.get('/api/v1/tests?where=id:%s' % pt_id).data
    db_t_id = db_t['tests'][0]['id']
    assert db_t_id == pt_id

    db_t = admin.get('/api/v1/tests?where=name:pname1').data
    db_t_id = db_t['tests'][0]['id']
    assert db_t_id == pt_id


def test_get_all_tests_with_pagination(admin):
    # create 4 components types and check meta data count
    admin.post('/api/v1/tests', data={'name': 'pname1'})
    admin.post('/api/v1/tests', data={'name': 'pname2'})
    admin.post('/api/v1/tests', data={'name': 'pname3'})
    admin.post('/api/v1/tests', data={'name': 'pname4'})
    ts = admin.get('/api/v1/tests').data
    assert ts['_meta']['count'] == 4

    # verify limit and offset are working well
    ts = admin.get('/api/v1/tests?limit=2&offset=0').data
    assert len(ts['tests']) == 2

    ts = admin.get('/api/v1/tests?limit=2&offset=2').data
    assert len(ts['tests']) == 2

    # if offset is out of bound, the api returns an empty list
    ts = admin.get('/api/v1/tests?limit=5&offset=300')
    assert ts.status_code == 200
    assert ts.data['tests'] == []


def test_get_all_tests_with_sort(admin):
    # create 2 tests ordered by created time
    t_1 = admin.post('/api/v1/tests',
                     data={'name': 'pname1'}).data['test']
    t_2 = admin.post('/api/v1/tests',
                     data={'name': 'pname2'}).data['test']

    gts = admin.get('/api/v1/tests?sort=created_at').data
    assert gts['tests'] == [t_1, t_2]

    # test in reverse order
    gts = admin.get('/api/v1/tests?sort=-created_at').data
    assert gts['tests'] == [t_2, t_1]


def test_get_test_by_id_or_name(admin):
    pt = admin.post('/api/v1/tests',
                    data={'name': 'pname'}).data
    pt_id = pt['test']['id']

    # get by uuid
    created_t = admin.get('/api/v1/tests/%s' % pt_id)
    assert created_t.status_code == 200

    created_t = created_t.data
    assert created_t['test']['id'] == pt_id

    # get by name
    created_t = admin.get('/api/v1/tests/pname')
    assert created_t.status_code == 200

    created_t = created_t.data
    assert created_t['test']['id'] == pt_id


def test_get_test_not_found(admin):
    result = admin.get('/api/v1/tests/ptdr')
    assert result.status_code == 404


def test_put_tests(admin):
    pt = admin.post('/api/v1/tests', data={'name': 'pname'})
    assert pt.status_code == 201

    pt_etag = pt.headers.get("ETag")

    gt = admin.get('/api/v1/tests/pname')
    assert gt.status_code == 200

    ppt = admin.put('/api/v1/tests/pname',
                    data={'name': 'nname'},
                    headers={'If-match': pt_etag})
    assert ppt.status_code == 204

    gt = admin.get('/api/v1/tests/pname')
    assert gt.status_code == 404

    gt = admin.get('/api/v1/tests/nname')
    assert gt.status_code == 200


def test_delete_test_by_id(admin):
    pt = admin.post('/api/v1/tests',
                    data={'name': 'pname'})
    pt_etag = pt.headers.get("ETag")
    pt_id = pt.data['test']['id']
    assert pt.status_code == 201

    created_t = admin.get('/api/v1/tests/%s' % pt_id)
    assert created_t.status_code == 200

    deleted_t = admin.delete('/api/v1/tests/%s' % pt_id,
                             headers={'If-match': pt_etag})
    assert deleted_t.status_code == 204

    gt = admin.get('/api/v1/tests/%s' % pt_id)
    assert gt.status_code == 404


def test_delete_test_not_found(admin):
    result = admin.delete('/api/v1/tests/ptdr',
                          headers={'If-match': 'mdr'})
    assert result.status_code == 404
