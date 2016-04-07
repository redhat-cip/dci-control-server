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


def test_create_jobdefinitions(admin, test_id, topic_id):
    jd = admin.post('/api/v1/jobdefinitions',
                    data={'name': 'pname', 'test_id': test_id,
                          'topic_id': topic_id}).data
    jd_id = jd['jobdefinition']['id']
    jd = admin.get('/api/v1/jobdefinitions/%s' % jd_id).data
    assert jd['jobdefinition']['name'] == 'pname'


def test_get_all_jobdefinitions(admin, test_id, topic_id):
    data = {'name': 'pname1', 'test_id': test_id, 'topic_id': topic_id}
    jd_1 = admin.post('/api/v1/jobdefinitions', data=data).data
    jd_1_id = jd_1['jobdefinition']['id']

    data = {'name': 'pname2', 'test_id': test_id, 'topic_id': topic_id}
    jd_2 = admin.post('/api/v1/jobdefinitions', data=data).data
    jd_2_id = jd_2['jobdefinition']['id']

    db_all_jds = admin.get(
        '/api/v1/topics/%s/jobdefinitions?sort=created_at' % topic_id).data
    db_all_jds = db_all_jds['jobdefinitions']
    db_all_jds_ids = [db_jd['id'] for db_jd in db_all_jds]

    assert db_all_jds_ids == [jd_1_id, jd_2_id]


def test_get_all_jobdefinitions_not_in_topic(admin):
    topic = admin.post('/api/v1/topics', data={'name': 'topic_test'}).data
    topic_id = topic['topic']['id']
    status_code = admin.get(
        '/api/v1/topics/%s/jobdefinitions' % topic_id).status_code
    assert status_code == 412


def test_get_all_jobdefinitions_with_pagination(admin, test_id, topic_id):
    # create 4 jobdefinition types and check meta count
    data = {'name': 'pname1', 'test_id': test_id, 'topic_id': topic_id}
    admin.post('/api/v1/jobdefinitions', data=data)
    data = {'name': 'pname2', 'test_id': test_id, 'topic_id': topic_id}
    admin.post('/api/v1/jobdefinitions', data=data)
    data = {'name': 'pname3', 'test_id': test_id, 'topic_id': topic_id}
    admin.post('/api/v1/jobdefinitions', data=data)
    data = {'name': 'pname4', 'test_id': test_id, 'topic_id': topic_id}
    admin.post('/api/v1/jobdefinitions', data=data)

    # check meta count
    jds = admin.get('/api/v1/topics/%s/jobdefinitions' % topic_id).data
    assert jds['_meta']['count'] == 4

    # verify limit and offset are working well
    jds = admin.get(
        '/api/v1/topics/%s/jobdefinitions?limit=2&offset=0' % topic_id).data
    assert len(jds['jobdefinitions']) == 2

    jds = admin.get(
        '/api/v1/topics/%s/jobdefinitions?limit=2&offset=2' % topic_id).data
    assert len(jds['jobdefinitions']) == 2

    # if offset is out of bound, the api returns an empty list
    jds = admin.get(
        '/api/v1/topics/%s/jobdefinitions?limit=5&offset=300' % topic_id)
    assert jds.status_code == 200
    assert jds.data['jobdefinitions'] == []


def test_get_all_jobdefinitions_with_embed(admin, test_id, topic_id):
    # create 2 jobdefinition and check meta data count
    data = {'name': 'pname1', 'test_id': test_id, 'topic_id': topic_id}
    admin.post('/api/v1/jobdefinitions', data=data)
    data = {'name': 'pname2', 'test_id': test_id, 'topic_id': topic_id}
    admin.post('/api/v1/jobdefinitions', data=data)

    # verify embed
    jds = admin.get(
        '/api/v1/topics/%s/jobdefinitions?embed=test' % topic_id).data

    for jobdefinition in jds['jobdefinitions']:
        assert 'test_id' not in jobdefinition
        assert 'test' in jobdefinition
        assert jobdefinition['test']['id'] == test_id


def test_get_all_jobdefinitions_with_embed_not_valid(admin, test_id, topic_id):
    jds = admin.get('/api/v1/topics/%s/jobdefinitions?embed=mdr' % topic_id)
    assert jds.status_code == 400


def test_get_all_jobdefinitions_with_where(admin, test_id, topic_id):
    data = {'name': 'pname1', 'test_id': test_id, 'topic_id': topic_id}
    pjd = admin.post('/api/v1/jobdefinitions', data=data).data
    pjd_id = pjd['jobdefinition']['id']

    db_jd = admin.get(
        '/api/v1/topics/%s/jobdefinitions?where=id:%s' %
        (topic_id, pjd_id)).data
    db_jd_id = db_jd['jobdefinitions'][0]['id']
    assert db_jd_id == pjd_id

    db_jd = admin.get(
        '/api/v1/topics/%s/jobdefinitions?where=name:pname1' % topic_id).data
    db_jd_id = db_jd['jobdefinitions'][0]['id']
    assert db_jd_id == pjd_id


def test_where_invalid(admin, topic_id):
    err = admin.get('/api/v1/topics/%s/jobdefinitions?where=id' % topic_id)

    assert err.status_code == 400
    assert err.data == {
        'status_code': 400,
        'message': 'Invalid where key: "id"',
        'payload': {
            'error': 'where key must have the following form "key:value"'
        }
    }


def test_get_jobdefinition_by_id_or_name(admin, test_id, topic_id):
    pjd = admin.post('/api/v1/jobdefinitions',
                     data={'name': 'pname', 'test_id': test_id,
                           'topic_id': topic_id}).data
    pjd_id = pjd['jobdefinition']['id']

    # get by uuid
    created_ct = admin.get('/api/v1/jobdefinitions/%s' % pjd_id)
    assert created_ct.status_code == 200

    created_ct = created_ct.data
    assert created_ct['jobdefinition']['id'] == pjd_id

    # get by name
    created_ct = admin.get('/api/v1/jobdefinitions/pname')
    assert created_ct.status_code == 200

    created_ct = created_ct.data
    assert created_ct['jobdefinition']['id'] == pjd_id


def test_get_jobdefinition_not_found(admin):
    result = admin.get('/api/v1/jobdefinitions/ptdr')
    assert result.status_code == 404


def test_put_jobdefinitions(admin, test_id, topic_id):
    jd = admin.post('/api/v1/jobdefinitions',
                    data={'name': 'pname', 'test_id': test_id,
                          'topic_id': topic_id}).data
    jd_id = jd['jobdefinition']['id']
    jd = admin.get('/api/v1/jobdefinitions/%s' % jd_id).data
    jd_etag = jd['jobdefinition']['etag']
    assert jd['jobdefinition']['name'] == 'pname'

    ppt = admin.put('/api/v1/jobdefinitions/%s' % jd_id,
                    data={'active': False}, headers={'If-match': jd_etag})
    assert ppt.status_code == 204

    gt = admin.get('/api/v1/jobdefinitions/%s' % jd_id).data
    gt_etag = gt['jobdefinition']['etag']
    assert gt['jobdefinition']['name'] == 'pname'
    assert gt['jobdefinition']['active'] is False

    ppt = admin.put('/api/v1/jobdefinitions/%s' % jd_id,
                    data={'comment': 'A comment'},
                    headers={'If-match': gt_etag})
    assert ppt.status_code == 204

    gt = admin.get('/api/v1/jobdefinitions/%s' % jd_id).data
    assert gt['jobdefinition']['name'] == 'pname'
    assert gt['jobdefinition']['active'] is False
    assert gt['jobdefinition']['comment'] == 'A comment'


def test_delete_jobdefinition_by_id(admin, test_id, topic_id):
    data = {'name': 'pname', 'test_id': test_id, 'topic_id': topic_id}
    pjd = admin.post('/api/v1/jobdefinitions', data=data)
    pct_etag = pjd.headers.get("ETag")
    pjd_id = pjd.data['jobdefinition']['id']
    assert pjd.status_code == 201

    url = '/api/v1/jobdefinitions/%s' % pjd_id

    created_jd = admin.get(url)
    assert created_jd.status_code == 200

    deleted_jd = admin.delete(url, headers={'If-match': pct_etag})
    assert deleted_jd.status_code == 204

    gjd = admin.get('/api/v1/jobdefinitions/%s' % pjd_id)
    assert gjd.status_code == 404


def test_get_all_jobdefinitions_with_sort(admin, test_id, topic_id):
    # create 4 jobdefinitions ordered by created time
    jd_1_1 = admin.post('/api/v1/jobdefinitions',
                        data={'name': "pname1", 'priority': 0,
                              'test_id': test_id,
                              'topic_id': topic_id}).data['jobdefinition']
    jd_1_2 = admin.post('/api/v1/jobdefinitions',
                        data={'name': "pname2", 'priority': 0,
                              'test_id': test_id,
                              'topic_id': topic_id}).data['jobdefinition']
    jd_2_1 = admin.post('/api/v1/jobdefinitions',
                        data={'name': "pname3", 'priority': 1,
                              'test_id': test_id,
                              'topic_id': topic_id}).data['jobdefinition']
    jd_2_2 = admin.post('/api/v1/jobdefinitions',
                        data={'name': "pname4", 'priority': 1,
                              'test_id': test_id,
                              'topic_id': topic_id}).data['jobdefinition']

    jds = admin.get(
        '/api/v1/topics/%s/jobdefinitions?sort=created_at' % topic_id).data
    assert jds['jobdefinitions'] == [jd_1_1, jd_1_2, jd_2_1, jd_2_2]

    # sort by priority first and then reverse by created_at
    jds = admin.get(
        '/api/v1/topics/%s/jobdefinitions?sort=priority,-created_at' %
        topic_id).data
    assert jds['jobdefinitions'] == [jd_1_2, jd_1_1, jd_2_2, jd_2_1]


def test_get_jobdefinition_with_embed(admin, test_id, topic_id):
    pt = admin.get('/api/v1/tests/%s' % test_id).data
    data = {'name': 'pname', 'test_id': test_id, 'topic_id': topic_id}
    pjd = admin.post('/api/v1/jobdefinitions', data=data).data
    del pjd['jobdefinition']['test_id']
    pjd['jobdefinition'][u'test'] = pt['test']

    # verify embed
    jd_embed = admin.get('/api/v1/jobdefinitions/pname?embed=test').data
    assert pjd == jd_embed


def test_get_jobdefinition_with_embed_not_valid(admin, test_id):
    jds = admin.get('/api/v1/jobdefinitions/pname?embed=mdr')
    assert jds.status_code == 400


def test_delete_jobdefinition_not_found(admin):
    url = '/api/v1/jobdefinitions/ptdr'
    result = admin.delete(url, headers={'If-match': 'mdr'})
    assert result.status_code == 404


# Tests for jobdefinition and components management
def test_add_component_to_jobdefinitions_and_get(admin, test_id, topic_id):
    # create a jobdefinition
    data = {'name': 'pname', 'test_id': test_id, 'topic_id': topic_id}
    pjd = admin.post('/api/v1/jobdefinitions', data=data).data
    pjd_id = pjd['jobdefinition']['id']

    # create a component
    data = {'name': 'pname', 'type': 'gerrit_review', 'topic_id': topic_id}
    pc = admin.post('/api/v1/components', data=data).data
    pc_id = pc['component']['id']

    url = '/api/v1/jobdefinitions/%s/components' % pjd_id
    # add component to jobdefinition
    add_data = admin.post(url, data={'component_id': pc_id}).data
    assert add_data['jobdefinition_id'] == pjd_id
    assert add_data['component_id'] == pc_id

    # get component from jobdefinition
    component_from_jobdefinition = admin.get(url).data
    assert component_from_jobdefinition['_meta']['count'] == 1
    assert component_from_jobdefinition['components'][0] == pc['component']


def test_delete_component_from_jobdefinition(admin, test_id, topic_id):
    # create a jobdefinition
    data = {'name': 'pname', 'test_id': test_id, 'topic_id': topic_id}
    pjd = admin.post('/api/v1/jobdefinitions', data=data).data
    pjd_id = pjd['jobdefinition']['id']

    # create a component
    data = {'name': 'pname', 'type': 'gerrit_review', 'topic_id': topic_id}
    pc = admin.post('/api/v1/components', data=data).data
    pc_id = pc['component']['id']

    # add component to jobdefinition
    url = '/api/v1/jobdefinitions/%s/components' % pjd_id
    admin.post(url, data={'component_id': pc_id})
    component_from_jobdefinition = admin.get(
        '/api/v1/jobdefinitions/%s/components' % pjd_id).data
    assert component_from_jobdefinition['_meta']['count'] == 1

    # delete component from jobdefinition
    admin.delete('/api/v1/jobdefinitions/%s/components/%s' % (pjd_id, pc_id))
    component_from_jobdefinition = admin.get(url).data
    assert component_from_jobdefinition['_meta']['count'] == 0

    # verify component still exist on /components
    c = admin.get('/api/v1/components/%s' % pc_id)
    assert c.status_code == 200
