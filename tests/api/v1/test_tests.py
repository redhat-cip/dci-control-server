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
import mock

from dci.stores.swift import Swift
from dci.common import utils

SWIFT = 'dci.stores.swift.Swift'


def test_create_tests(user, team_user_id):
    pt = user.post('/api/v1/tests',
                   data={'name': 'pname', 'team_id': team_user_id}).data
    pt_id = pt['test']['id']
    gt = user.get('/api/v1/tests/%s' % pt_id).data
    assert gt['test']['name'] == 'pname'


def test_create_tests_already_exist(user, team_user_id):
    pstatus_code = user.post('/api/v1/tests',
                             data={'name': 'pname',
                                   'team_id': team_user_id}).status_code
    assert pstatus_code == 201

    pstatus_code = user.post('/api/v1/tests',
                             data={'name': 'pname',
                                   'team_id': team_user_id}).status_code
    assert pstatus_code == 409


def test_get_all_tests_from_topic(admin, user, team_user_id, topic_user_id):
    test_1 = user.post('/api/v1/tests', data={'name': 'pname1',
                                              'team_id': team_user_id}).data
    test_2 = user.post('/api/v1/tests', data={'name': 'pname2',
                                              'team_id': team_user_id}).data

    admin.post('/api/v1/topics/%s/tests' % topic_user_id,
               data={'test_id': test_1['test']['id']})
    admin.post('/api/v1/topics/%s/tests' % topic_user_id,
               data={'test_id': test_2['test']['id']})

    db_all_tests = user.get(
        '/api/v1/topics/%s/tests?sort=created_at' % topic_user_id).data

    db_all_tests = db_all_tests['tests']
    db_all_tests_ids = [db_t['id'] for db_t in db_all_tests]

    assert db_all_tests_ids == [test_1['test']['id'], test_2['test']['id']]


def test_get_all_tests(admin, user, team_user_id, topic_user_id):
    test_1 = user.post('/api/v1/tests', data={'name': 'pname1',
                                              'team_id': team_user_id}).data
    test_2 = user.post('/api/v1/tests', data={'name': 'pname2',
                                              'team_id': team_user_id}).data

    admin.post('/api/v1/topics/%s/tests' % topic_user_id,
               data={'test_id': test_1['test']['id']})
    admin.post('/api/v1/topics/%s/tests' % topic_user_id,
               data={'test_id': test_2['test']['id']})

    # get tests by user
    db_all_tests = user.get('/api/v1/topics/%s/tests' % topic_user_id).data

    db_all_tests = db_all_tests['tests']
    assert len(db_all_tests) == 2
    db_all_tests_ids = set([db_t['id'] for db_t in db_all_tests])

    assert db_all_tests_ids == {test_1['test']['id'], test_2['test']['id']}


def test_get_all_tests_not_in_topic(admin, user, product_openstack):
    topic = admin.post('/api/v1/topics',
                       data={'name': 'topic_test',
                             'product_id': product_openstack['id'],
                             'component_types': ['type1', 'type2']}).data
    topic_id = topic['topic']['id']
    res = user.get(
        '/api/v1/topics/%s/tests' % topic_id)
    assert res.status_code == 401
    assert res.data['message'] == 'Operation not authorized.'


def test_get_all_tests_with_pagination(admin, user, team_user_id,
                                       topic_user_id):
    # create 4 components types and check meta data count
    test1 = admin.post('/api/v1/tests',
                       data={'name': 'pname1', 'team_id': team_user_id}).data
    test2 = admin.post('/api/v1/tests',
                       data={'name': 'pname2', 'team_id': team_user_id}).data
    test3 = admin.post('/api/v1/tests',
                       data={'name': 'pname3', 'team_id': team_user_id}).data
    test4 = admin.post('/api/v1/tests',
                       data={'name': 'pname4', 'team_id': team_user_id}).data

    admin.post('/api/v1/topics/%s/tests' % topic_user_id,
               data={'test_id': test1['test']['id']})
    admin.post('/api/v1/topics/%s/tests' % topic_user_id,
               data={'test_id': test2['test']['id']})
    admin.post('/api/v1/topics/%s/tests' % topic_user_id,
               data={'test_id': test3['test']['id']})
    admin.post('/api/v1/topics/%s/tests' % topic_user_id,
               data={'test_id': test4['test']['id']})
    ts = admin.get('/api/v1/topics/%s/tests' % topic_user_id).data

    assert ts['_meta']['count'] == 4

    # verify limit and offset are working well
    ts = user.get(
        '/api/v1/topics/%s/tests?limit=2&offset=0' % topic_user_id).data
    assert len(ts['tests']) == 2

    ts = user.get(
        '/api/v1/topics/%s/tests?limit=2&offset=2' % topic_user_id).data
    assert len(ts['tests']) == 2

    # if offset is out of bound, the api returns an empty list
    ts = user.get('/api/v1/topics/%s/tests?limit=5&offset=300' % topic_user_id)
    assert ts.status_code == 200
    assert ts.data['tests'] == []


def test_get_all_tests_with_sort(admin, user, team_user_id, topic_user_id):
    # create 2 tests ordered by created time
    t_1 = admin.post('/api/v1/tests',
                     data={'name': 'pname1',
                           'team_id': team_user_id}).data['test']
    t_2 = admin.post('/api/v1/tests',
                     data={'name': 'pname2',
                           'team_id': team_user_id}).data['test']

    admin.post('/api/v1/topics/%s/tests' % topic_user_id,
               data={'test_id': t_1['id']})
    admin.post('/api/v1/topics/%s/tests' % topic_user_id,
               data={'test_id': t_2['id']})

    gts = user.get('/api/v1/topics/%s/tests?sort=created_at' %
                   topic_user_id).data
    assert gts['tests'][0]['id'] == t_1['id']
    assert gts['tests'][1]['id'] == t_2['id']

    # test in reverse order
    gts = user.get('/api/v1/topics/%s/tests?sort=-created_at' %
                   topic_user_id).data
    assert gts['tests'][0]['id'] == t_2['id']
    assert gts['tests'][1]['id'] == t_1['id']


def test_get_test_by_id(admin, team_user_id):
    pt = admin.post('/api/v1/tests', data={'name': 'pname',
                                           'team_id': team_user_id}).data
    pt_id = pt['test']['id']

    # get by uuid
    created_t = admin.get('/api/v1/tests/%s' % pt_id)
    assert created_t.status_code == 200

    created_t = created_t.data
    assert created_t['test']['id'] == pt_id


def test_get_test_not_found(admin):
    result = admin.get('/api/v1/tests/ptdr')
    assert result.status_code == 404


def test_get_tests_from_teams(admin, user, team_user_id, team_id):
    # Create two test 1 for each team
    test_1 = admin.post('/api/v1/tests',
                        data={'name': 'pname1',
                              'team_id': team_user_id}).data['test']
    test_id_1 = test_1['id']
    test_2 = admin.post('/api/v1/tests',
                        data={'name': 'pname2',
                              'team_id': team_id}).data['test']
    test_id_2 = test_2['id']

    # Verify user can get tests in his team
    t_tests = user.get('/api/v1/tests/%s' % test_id_1)
    assert t_tests.status_code == 200
    assert t_tests.data['test']['id'] == test_id_1

    # Verify user can't get tests from other teams
    t_tests = user.get('/api/v1/tests/%s' % test_id_2)
    assert t_tests.status_code == 401


def test_get_tests_from_remotecis(admin, user, team_user_id, team_id):
    # Create 2 remoteCI
    rci_1 = user.post('/api/v1/remotecis',
                      data={'name': 'foo', 'team_id': team_user_id})
    rci_id_1 = rci_1.data['remoteci']['id']
    rci_2 = admin.post('/api/v1/remotecis',
                       data={'name': 'foo2', 'team_id': team_id})
    rci_id_2 = rci_2.data['remoteci']['id']

    # Create two tests
    test_1 = admin.post('/api/v1/tests',
                        data={'name': 'pname1',
                              'team_id': team_user_id}).data['test']
    test_id_1 = test_1['id']
    test_2 = admin.post('/api/v1/tests',
                        data={'name': 'pname2',
                              'team_id': team_user_id}).data['test']
    test_id_2 = test_2['id']

    # Attach tests to remote CI
    admin.post('/api/v1/remotecis/%s/tests' % rci_id_1,
               data={'test_id': test_id_1})
    admin.post('/api/v1/remotecis/%s/tests' % rci_id_2,
               data={'test_id': test_id_2})

    # Verify user can access his remoteci test
    t_tests = user.get('/api/v1/remotecis/%s/tests' % rci_id_1)
    assert t_tests.status_code == 200
    # Verify user can access the test linked to remoteci
    assert t_tests.data['tests'][0]['id'] == test_id_1

    # Verify user can't access to other remoteci tests
    t_tests = user.get('/api/v1/remoteci/%s/tests' % rci_id_2)
    assert t_tests.status_code == 404


def test_get_tests_from_topics(admin, user, team_user_id, team_id, product):
    # Create two test 1 for each team
    test_1 = admin.post('/api/v1/tests',
                        data={'name': 'pname1',
                              'team_id': team_user_id}).data['test']
    test_id_1 = test_1['id']
    test_2 = admin.post('/api/v1/tests',
                        data={'name': 'pname2',
                              'team_id': team_id}).data['test']
    test_id_2 = test_2['id']

    # Create two different topic
    topic_1 = admin.post('/api/v1/topics',
                         data={'name': 'topic_test_1',
                               'product_id': product['id'],
                               'component_types': ['type1', 'type2']}).data
    topic_id_1 = topic_1['topic']['id']
    topic_2 = admin.post('/api/v1/topics',
                         data={'name': 'topic_test_2',
                               'product_id': product['id'],
                               'component_types': ['type1', 'type2']}).data
    topic_id_2 = topic_2['topic']['id']

    # Attach the user's team to topic 1
    admin.post('/api/v1/topics/%s/teams' % topic_id_1,
               data={'team_id': team_user_id})

    # Attach tests to topics
    admin.post('/api/v1/topics/%s/tests' % topic_id_1,
               data={'test_id': test_id_1})
    admin.post('/api/v1/topics/%s/tests' % topic_id_2,
               data={'test_id': test_id_2})

    # Verify user can access his topic test
    t_tests = user.get('/api/v1/topics/%s/tests?sort=created_at' % topic_id_1)
    assert t_tests.status_code == 200
    # Verify user can access the test linked in the topic
    assert t_tests.data['tests'][0]['id'] == test_id_1

    # Verify user can't access to other topic tests
    t_tests = user.get('/api/v1/topics/%s/tests' % topic_id_2)
    assert t_tests.status_code == 401
    assert t_tests.data['message'] == 'Operation not authorized.'


def test_delete_test_by_id(admin, team_user_id):
    pt = admin.post('/api/v1/tests', data={'name': 'pname',
                                           'team_id': team_user_id})
    pt_id = pt.data['test']['id']
    assert pt.status_code == 201

    created_t = admin.get('/api/v1/tests/%s' % pt_id)
    assert created_t.status_code == 200
    pt_etag = created_t.data['test']['etag']

    deleted_t = admin.delete('/api/v1/tests/%s' % pt_id,
                             headers={'If-match': pt_etag})
    assert deleted_t.status_code == 204

    gt = admin.get('/api/v1/tests/%s' % pt_id)
    assert gt.status_code == 404


def test_delete_test_not_found(admin):
    result = admin.delete('/api/v1/tests/ptdr',
                          headers={'If-match': 'eefrwqafeqawfqafeq'})
    assert result.status_code == 404


def test_delete_test_archive_dependencies(admin, job_user_id, team_user_id):
    with mock.patch(SWIFT, spec=Swift) as mock_swift:

        mockito = mock.MagicMock()

        head_result = {
            'etag': utils.gen_etag(),
            'content-type': "stream",
            'content-length': 7
        }

        mockito.head.return_value = head_result
        mock_swift.return_value = mockito

        test = admin.post('/api/v1/tests', data={'name': 'pname',
                                                 'team_id': team_user_id})
        test_id = test.data['test']['id']
        assert test.status_code == 201
        test_etag = \
            admin.get('/api/v1/tests/%s' % test_id).data['test']['etag']

        file = admin.post('/api/v1/files',
                          headers={
                              'DCI-NAME': 'kikoolol',
                              'DCI-JOB-ID': job_user_id,
                              'DCI-TEST-ID': test_id
                          },
                          data='content')

        file_id = file.data['file']['id']
        assert file.status_code == 201

        deleted_test = admin.delete('/api/v1/tests/%s' % test_id,
                                    headers={'If-match': test_etag})

        assert deleted_test.status_code == 204

        deleted_file = admin.get('/api/v1/files/%s' % file_id)
        assert deleted_file.status_code == 404


def test_change_test(admin, test_id):
    t = admin.get('/api/v1/tests/' + test_id).data['test']
    data = {'state': 'inactive'}
    r = admin.put('/api/v1/tests/' + test_id,
                  data=data,
                  headers={'If-match': t['etag']})
    assert r.status_code == 204
    current_test = admin.get('/api/v1/tests/' + test_id).data['test']
    assert current_test['state'] == 'inactive'


def test_change_test_to_invalid_state(admin, test_id):
    t = admin.get('/api/v1/tests/' + test_id).data['test']
    data = {'state': 'kikoolol'}
    r = admin.put('/api/v1/tests/' + test_id,
                  data=data,
                  headers={'If-match': t['etag']})
    assert r.status_code == 400
    current_test = admin.get('/api/v1/tests/' + test_id)
    assert current_test.status_code == 200
    assert current_test.data['test']['state'] == 'active'


def test_success_update_field_by_field(admin, test_id):
    t = admin.get('/api/v1/tests/%s' % test_id).data['test']

    admin.put('/api/v1/tests/%s' % test_id,
              data={'state': 'inactive'},
              headers={'If-match': t['etag']})

    t = admin.get('/api/v1/tests/%s' % test_id).data['test']

    assert t['name'] == 'pname'
    assert t['state'] == 'inactive'
    assert t['data'] == {}

    admin.put('/api/v1/tests/%s' % test_id,
              data={'name': 'pname2'},
              headers={'If-match': t['etag']})

    t = admin.get('/api/v1/tests/%s' % test_id).data['test']

    assert t['name'] == 'pname2'
    assert t['state'] == 'inactive'
    assert t['data'] == {}

    admin.put('/api/v1/tests/%s' % test_id,
              data={'data': {'test': 'toto'}},
              headers={'If-match': t['etag']})

    t = admin.get('/api/v1/tests/%s' % test_id).data['test']

    assert t['name'] == 'pname2'
    assert t['state'] == 'inactive'
    assert t['data'] == {'test': 'toto'}
