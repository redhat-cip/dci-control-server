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
import uuid


def test_create_components(admin, topic_id):
    data = {
        'name': 'pname',
        'type': 'gerrit_review',
        'url': 'http://example.com/',
        'topic_id': topic_id}
    pc = admin.post('/api/v1/components', data=data).data
    pc_id = pc['component']['id']
    gc = admin.get('/api/v1/components/%s' % pc_id).data
    assert gc['component']['name'] == 'pname'


def test_create_components_already_exist(admin, topic_id):
    data = {'name': 'pname', 'type': 'gerrit_review', 'topic_id': topic_id}
    pstatus_code = admin.post('/api/v1/components', data=data).status_code
    assert pstatus_code == 201

    data = {'name': 'pname', 'type': 'gerrit_review', 'topic_id': topic_id}
    pstatus_code = admin.post('/api/v1/components', data=data).status_code
    assert pstatus_code == 422


def test_create_components_with_same_name_on_different_topics(admin, topic_id):
    data = {'name': 'pname', 'type': 'gerrit_review', 'topic_id': topic_id}
    pstatus_code = admin.post('/api/v1/components', data=data).status_code
    assert pstatus_code == 201

    topic2 = admin.post('/api/v1/topics', data={'name': 'tname'}).data
    topic_id2 = topic2['topic']['id']

    data = {'name': 'pname', 'type': 'gerrit_review', 'topic_id': topic_id2}
    pstatus_code = admin.post('/api/v1/components', data=data).status_code
    assert pstatus_code == 201


def test_create_components_with_same_name_on_same_topics(admin, topic_id):
    data = {'name': 'pname', 'type': 'gerrit_review', 'topic_id': topic_id}
    pstatus_code = admin.post('/api/v1/components', data=data).status_code
    assert pstatus_code == 201

    data = {'name': 'pname', 'type': 'gerrit_review', 'topic_id': topic_id}
    pstatus_code = admin.post('/api/v1/components', data=data).status_code
    assert pstatus_code == 422


def test_get_all_components(admin, topic_id):
    created_c_ids = []
    for i in range(5):
        pc = admin.post('/api/v1/components',
                        data={'name': 'pname%s' % uuid.uuid4(),
                              'type': 'gerrit_review',
                              'topic_id': topic_id}).data
        created_c_ids.append(pc['component']['id'])
    created_c_ids.sort()

    db_all_cs = admin.get('/api/v1/topics/%s/components' % topic_id).data
    db_all_cs = db_all_cs['components']
    db_all_cs_ids = [db_ct['id'] for db_ct in db_all_cs]
    db_all_cs_ids.sort()

    assert db_all_cs_ids == created_c_ids


def test_get_all_components_not_in_topic(admin):
    topic = admin.post('/api/v1/topics', data={'name': 'topic_test'}).data
    topic_id = topic['topic']['id']
    status_code = admin.get(
        '/api/v1/topics/%s/components' % topic_id).status_code
    assert status_code == 412


def test_get_all_components_with_pagination(admin, topic_id):
    # create 20 component types and check meta data count
    for i in range(20):
        admin.post('/api/v1/components',
                   data={'name': 'pname%s' % uuid.uuid4(),
                         'type': 'gerrit_review',
                         'topic_id': topic_id})
    cs = admin.get('/api/v1/topics/%s/components' % topic_id).data
    assert cs['_meta']['count'] == 20

    # verify limit and offset are working well
    for i in range(4):
        cs = admin.get(
            '/api/v1/topics/%s/components?limit=5&offset=%s' %
            (topic_id, (i * 5))).data
        assert len(cs['components']) == 5

    # if offset is out of bound, the api returns an empty list
    cs = admin.get(
        '/api/v1/topics/%s/components?limit=5&offset=300' % topic_id)
    assert cs.status_code == 200
    assert cs.data['components'] == []


def test_get_all_components_with_where(admin, topic_id):
    pc = admin.post('/api/v1/components',
                    data={'name': 'pname1',
                          'type': 'gerrit_review',
                          'topic_id': topic_id}).data
    pc_id = pc['component']['id']

    db_c = admin.get(
        '/api/v1/topics/%s/components?where=id:%s' % (topic_id, pc_id)).data
    db_c_id = db_c['components'][0]['id']
    assert db_c_id == pc_id

    db_c = admin.get(
        '/api/v1/topics/%s/components?where=name:pname1' % topic_id).data
    db_c_id = db_c['components'][0]['id']
    assert db_c_id == pc_id


def test_where_invalid(admin, topic_id):
    err = admin.get('/api/v1/topics/%s/components?where=id' % topic_id)

    assert err.status_code == 400
    assert err.data == {
        'status_code': 400,
        'message': 'Invalid where key: "id"',
        'payload': {
            'error': 'where key must have the following form "key:value"'
        }
    }


def test_get_component_by_id_or_name(admin, topic_id):
    data = {'name': 'pname', 'type': 'gerrit_review', 'topic_id': topic_id}
    pc = admin.post('/api/v1/components', data=data).data
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


def test_delete_component_by_id(admin, topic_id):
    data = {'name': 'pname', 'type': 'gerrit_review', 'topic_id': topic_id}
    pc = admin.post('/api/v1/components', data=data)
    pc_id = pc.data['component']['id']
    assert pc.status_code == 201

    created_ct = admin.get('/api/v1/components/%s' % pc_id)
    assert created_ct.status_code == 200

    deleted_ct = admin.delete('/api/v1/components/%s' % pc_id)
    assert deleted_ct.status_code == 204

    gct = admin.get('/api/v1/components/%s' % pc_id)
    assert gct.status_code == 404


def test_get_all_components_with_sort(admin, topic_id):
    # create 4 components ordered by created time
    data = {'name': "pname1", 'title': 'aaa',
            'type': 'gerrit_review',
            'topic_id': topic_id}
    ct_1_1 = admin.post('/api/v1/components', data=data).data['component']
    data = {'name': "pname2", 'title': 'aaa',
            'type': 'gerrit_review',
            'topic_id': topic_id}
    ct_1_2 = admin.post('/api/v1/components', data=data).data['component']
    data = {'name': "pname3", 'title': 'bbb',
            'type': 'gerrit_review',
            'topic_id': topic_id}
    ct_2_1 = admin.post('/api/v1/components', data=data).data['component']
    data = {'name': "pname4", 'title': 'bbb',
            'type': 'gerrit_review',
            'topic_id': topic_id}
    ct_2_2 = admin.post('/api/v1/components', data=data).data['component']

    cts = admin.get(
        '/api/v1/topics/%s/components?sort=created_at' % topic_id).data
    assert cts['components'] == [ct_1_1, ct_1_2, ct_2_1, ct_2_2]

    # sort by title first and then reverse by created_at
    cts = admin.get(
        '/api/v1/topics/%s/components?sort=title,-created_at' % topic_id).data
    assert cts['components'] == [ct_1_2, ct_1_1, ct_2_2, ct_2_1]


def test_delete_component_not_found(admin):
    result = admin.delete('/api/v1/components/ptdr',
                          headers={'If-match': 'mdr'})
    assert result.status_code == 404
