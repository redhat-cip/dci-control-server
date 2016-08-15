# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Red Hat, Inc
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


def test_create_tests(admin, team_id):
    pt = admin.post('/api/v1/tests',
                    data={'name': 'pname', 'team_id': team_id}).data
    pt_id = pt['test']['id']
    gt = admin.get('/api/v1/tests/%s' % pt_id).data
    assert gt['test']['name'] == 'pname'


def test_create_tests_already_exist(admin, team_id):
    pstatus_code = admin.post('/api/v1/tests',
                              data={'name': 'pname',
                                    'team_id': team_id}).status_code
    assert pstatus_code == 201

    pstatus_code = admin.post('/api/v1/tests',
                              data={'name': 'pname',
                                    'team_id': team_id}).status_code
    assert pstatus_code == 422


def test_get_all_tests(admin, team_id, topic_id):
    test_1 = admin.post('/api/v1/tests', data={'name': 'pname1',
                                               'team_id': team_id}).data
    test_2 = admin.post('/api/v1/tests', data={'name': 'pname2',
                                               'team_id': team_id}).data

    admin.post('/api/v1/topics/%s/tests' % topic_id,
               data={'test_id': test_1['test']['id']})
    admin.post('/api/v1/topics/%s/tests' % topic_id,
               data={'test_id': test_2['test']['id']})

    db_all_tests = admin.get(
        '/api/v1/topics/%s/tests?sort=created_at' % topic_id).data
    db_all_tests = db_all_tests['tests']
    db_all_tests_ids = [db_t['id'] for db_t in db_all_tests]

    assert db_all_tests_ids == [test_1['test']['id'], test_2['test']['id']]


def test_get_all_tests_not_in_topic(admin, user):
    topic = admin.post('/api/v1/topics', data={'name': 'topic_test'}).data
    topic_id = topic['topic']['id']
    status_code = user.get(
        '/api/v1/topics/%s/tests' % topic_id).status_code
    assert status_code == 412


def test_get_all_tests_with_pagination(admin, team_id, topic_id):
    # create 4 components types and check meta data count
    test1 = admin.post('/api/v1/tests',
                       data={'name': 'pname1', 'team_id': team_id}).data
    test2 = admin.post('/api/v1/tests',
                       data={'name': 'pname2', 'team_id': team_id}).data
    test3 = admin.post('/api/v1/tests',
                       data={'name': 'pname3', 'team_id': team_id}).data
    test4 = admin.post('/api/v1/tests',
                       data={'name': 'pname4', 'team_id': team_id}).data
    print test1
    admin.post('/api/v1/topics/%s/tests' % topic_id,
               data={'test_id': test1['test']['id']})
    admin.post('/api/v1/topics/%s/tests' % topic_id,
               data={'test_id': test2['test']['id']})
    admin.post('/api/v1/topics/%s/tests' % topic_id,
               data={'test_id': test3['test']['id']})
    admin.post('/api/v1/topics/%s/tests' % topic_id,
               data={'test_id': test4['test']['id']})
    ts = admin.get('/api/v1/topics/%s/tests' % topic_id).data
    print ts
    assert ts['_meta']['count'] == 4

    # verify limit and offset are working well
    ts = admin.get(
        '/api/v1/topics/%s/tests?limit=2&offset=0' % topic_id).data
    assert len(ts['tests']) == 2

    ts = admin.get(
        '/api/v1/topics/%s/tests?limit=2&offset=2' % topic_id).data
    assert len(ts['tests']) == 2

    # if offset is out of bound, the api returns an empty list
    ts = admin.get('/api/v1/topics/%s/tests?limit=5&offset=300' % topic_id)
    assert ts.status_code == 200
    assert ts.data['tests'] == []


def test_get_all_tests_with_sort(admin, team_id, topic_id):
    # create 2 tests ordered by created time
    t_1 = admin.post('/api/v1/tests', data={'name': 'pname1',
                                            'team_id': team_id}).data['test']
    t_2 = admin.post('/api/v1/tests', data={'name': 'pname2',
                                            'team_id': team_id}).data['test']

    admin.post('/api/v1/topics/%s/tests' % topic_id,
               data={'test_id': t_1['id']})
    admin.post('/api/v1/topics/%s/tests' % topic_id,
               data={'test_id': t_2['id']})

    gts = admin.get('/api/v1/topics/%s/tests?sort=created_at' % topic_id).data
    assert gts['tests'][0]['id'] == t_1['id']
    assert gts['tests'][1]['id'] == t_2['id']

    # test in reverse order
    gts = admin.get('/api/v1/topics/%s/tests?sort=-created_at' % topic_id).data
    assert gts['tests'][0]['id'] == t_2['id']
    assert gts['tests'][1]['id'] == t_1['id']


def test_get_test_by_id_or_name(admin, team_id):
    pt = admin.post('/api/v1/tests', data={'name': 'pname',
                                           'team_id': team_id}).data
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


def test_delete_test_by_id(admin, team_id):
    pt = admin.post('/api/v1/tests', data={'name': 'pname',
                                           'team_id': team_id})
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
