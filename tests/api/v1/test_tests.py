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

from __future__ import unicode_literals


def test_create_tests(admin, topic_id):
    pt = admin.post('/api/v1/tests',
                    data={'name': 'pname', 'topic_id': topic_id}).data
    pt_id = pt['test']['id']
    gt = admin.get('/api/v1/tests/%s' % pt_id).data
    assert gt['test']['name'] == 'pname'


def test_create_tests_already_exist(admin, topic_id):
    pstatus_code = admin.post('/api/v1/tests',
                              data={'name': 'pname',
                                    'topic_id': topic_id}).status_code
    assert pstatus_code == 201

    pstatus_code = admin.post('/api/v1/tests',
                              data={'name': 'pname',
                                    'topic_id': topic_id}).status_code
    assert pstatus_code == 422


def test_get_all_tests(admin, topic_id):
    test_1 = admin.post('/api/v1/tests', data={'name': 'pname1',
                                               'topic_id': topic_id}).data
    test_2 = admin.post('/api/v1/tests', data={'name': 'pname2',
                                               'topic_id': topic_id}).data

    db_all_tests = admin.get('/api/v1/tests?sort=created_at').data
    db_all_tests = db_all_tests['tests']
    db_all_tests_ids = [db_t['id'] for db_t in db_all_tests]

    assert db_all_tests_ids == [test_1['test']['id'], test_2['test']['id']]


def test_get_all_tests_with_where(admin, topic_id):
    pt = admin.post('/api/v1/tests', data={'name': 'pname1',
                                           'topic_id': topic_id}).data
    pt_id = pt['test']['id']

    db_t = admin.get('/api/v1/tests?where=id:%s' % pt_id).data
    db_t_id = db_t['tests'][0]['id']
    assert db_t_id == pt_id

    db_t = admin.get('/api/v1/tests?where=name:pname1').data
    db_t_id = db_t['tests'][0]['id']
    assert db_t_id == pt_id


def test_where_invalid(admin):
    err = admin.get('/api/v1/tests?where=id')

    assert err.status_code == 400
    assert err.data == {
        'status_code': 400,
        'message': 'Invalid where key: "id"',
        'payload': {
            'error': 'where key must have the following form "key:value"'
        }
    }


def test_get_all_tests_with_pagination(admin, topic_id):
    # create 4 components types and check meta data count
    admin.post('/api/v1/tests', data={'name': 'pname1', 'topic_id': topic_id})
    admin.post('/api/v1/tests', data={'name': 'pname2', 'topic_id': topic_id})
    admin.post('/api/v1/tests', data={'name': 'pname3', 'topic_id': topic_id})
    admin.post('/api/v1/tests', data={'name': 'pname4', 'topic_id': topic_id})
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


def test_get_all_tests_with_sort(admin, topic_id):
    # create 2 tests ordered by created time
    t_1 = admin.post('/api/v1/tests', data={'name': 'pname1',
                                            'topic_id': topic_id}).data['test']
    t_2 = admin.post('/api/v1/tests', data={'name': 'pname2',
                                            'topic_id': topic_id}).data['test']

    gts = admin.get('/api/v1/tests?sort=created_at').data
    assert gts['tests'] == [t_1, t_2]

    # test in reverse order
    gts = admin.get('/api/v1/tests?sort=-created_at').data
    assert gts['tests'] == [t_2, t_1]


def test_get_test_by_id_or_name(admin, topic_id):
    pt = admin.post('/api/v1/tests', data={'name': 'pname',
                                           'topic_id': topic_id}).data
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


def test_delete_test_by_id(admin, topic_id):
    pt = admin.post('/api/v1/tests', data={'name': 'pname',
                                           'topic_id': topic_id})
    pt_id = pt.data['test']['id']
    assert pt.status_code == 201

    created_t = admin.get('/api/v1/tests/%s' % pt_id)
    assert created_t.status_code == 200

    deleted_t = admin.delete('/api/v1/tests/%s' % pt_id)
    assert deleted_t.status_code == 204

    gt = admin.get('/api/v1/tests/%s' % pt_id)
    assert gt.status_code == 404


def test_delete_test_not_found(admin):
    result = admin.delete('/api/v1/tests/ptdr')
    assert result.status_code == 404
