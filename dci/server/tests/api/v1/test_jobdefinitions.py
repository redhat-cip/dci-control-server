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
def t_id(admin):
    t = admin.post('/api/v1/tests',
                   data={'name': 'pname'}).data
    return t['test']['id']


def test_create_jobdefinitions(admin, t_id):
    jd = admin.post('/api/v1/jobdefinitions',
                    data={'name': 'pname', 'test_id': t_id}).data
    jd_id = jd['jobdefinition']['id']
    jd = admin.get('/api/v1/jobdefinitions/%s' % jd_id).data
    assert jd['jobdefinition']['name'] == 'pname'


# enabled later
def loltest_create_jobdefinitions_already_exist(admin, t_id):
    pstatus_code = admin.post('/api/v1/jobdefinitions',
                              data={'name': 'pname',
                                    'test_id': t_id}).status_code
    assert pstatus_code == 201

    pstatus_code = admin.post('/api/v1/jobdefinitions',
                              data={'name': 'pname',
                                    'test_id': t_id}).status_code
    assert pstatus_code == 400


def test_get_all_jobdefinitions(admin, t_id):
    created_jd_ids = []
    for i in range(5):
        pc = admin.post('/api/v1/jobdefinitions',
                        data={'name': 'pname%s' % uuid.uuid4(),
                              'test_id': t_id}).data
        created_jd_ids.append(pc['jobdefinition']['id'])
    created_jd_ids.sort()

    db_all_jds = admin.get('/api/v1/jobdefinitions').data
    db_all_jds = db_all_jds['jobdefinitions']
    db_all_jds_ids = [db_jd['id'] for db_jd in db_all_jds]
    db_all_jds_ids.sort()

    assert db_all_jds_ids == created_jd_ids


def test_get_all_jobdefinitions_with_pagination(admin, t_id):
    # create 20 jobdefinition types and check meta data count
    for i in range(20):
        admin.post('/api/v1/jobdefinitions',
                   data={'name': 'pname%s' % uuid.uuid4(),
                         'test_id': t_id})
    jds = admin.get('/api/v1/jobdefinitions').data
    assert jds['_meta']['count'] == 20

    # verify limit and offset are working well
    for i in range(4):
        jds = admin.get(
            '/api/v1/jobdefinitions?limit=5&offset=%s' % (i * 5)).data
        assert len(jds['jobdefinitions']) == 5

    # if offset is out of bound, the api returns an empty list
    jds = admin.get('/api/v1/jobdefinitions?limit=5&offset=300')
    assert jds.status_code == 200
    assert jds.data['jobdefinitions'] == []


def test_get_all_jobdefinitions_with_embed(admin, t_id):
    # create 20 jobdefinition types and check meta data count
    for i in range(10):
        admin.post('/api/v1/jobdefinitions',
                   data={'name': 'pname%s' % uuid.uuid4(),
                         'test_id': t_id})

    # verify embed
    jds = admin.get('/api/v1/jobdefinitions?embed=test').data

    for jobdefinition in jds['jobdefinitions']:
        assert 'test_id' not in jobdefinition
        assert 'test' in jobdefinition
        assert jobdefinition['test']['id'] == t_id


def test_get_all_jobdefinitions_with_embed_not_valid(admin, t_id):
    # create 20 jobdefinition types and check meta data count
    for i in range(10):
        admin.post('/api/v1/jobdefinitions',
                   data={'name': 'pname%s' % uuid.uuid4(),
                         'test_id': t_id})

    # verify embed
    jds = admin.get('/api/v1/jobdefinitions?embed=mdr')
    assert jds.status_code == 400


def test_get_all_jobdefinitions_with_where(admin, t_id):
    pjd = admin.post('/api/v1/jobdefinitions',
                     data={'name': 'pname1',
                           'test_id': t_id}).data
    pjd_id = pjd['jobdefinition']['id']

    db_jd = admin.get('/api/v1/jobdefinitions?where=id:%s' % pjd_id).data
    db_jd_id = db_jd['jobdefinitions'][0]['id']
    assert db_jd_id == pjd_id

    db_jd = admin.get('/api/v1/jobdefinitions?where=name:pname1').data
    db_jd_id = db_jd['jobdefinitions'][0]['id']
    assert db_jd_id == pjd_id


def test_get_jobdefinition_by_id_or_name(admin, t_id):
    pjd = admin.post('/api/v1/jobdefinitions',
                     data={'name': 'pname', 'test_id': t_id}).data
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


def test_delete_jobdefinition_by_id(admin, t_id):
    pjd = admin.post('/api/v1/jobdefinitions',
                     data={'name': 'pname', 'test_id': t_id})
    pct_etag = pjd.headers.get("ETag")
    pjd_id = pjd.data['jobdefinition']['id']
    assert pjd.status_code == 201

    created_jd = admin.get('/api/v1/jobdefinitions/%s' % pjd_id)
    assert created_jd.status_code == 200

    deleted_jd = admin.delete('/api/v1/jobdefinitions/%s' % pjd_id,
                              headers={'If-match': pct_etag})
    assert deleted_jd.status_code == 204

    gjd = admin.get('/api/v1/jobdefinitions/%s' % pjd_id)
    assert gjd.status_code == 404


def test_get_all_jobdefinitions_with_sort(admin, t_id):
    # create 4 jobdefinitions ordered by created time
    jd_1_1 = admin.post('/api/v1/jobdefinitions',
                        data={'name': "pname1", 'priority': 0,
                              'test_id': t_id}).data['jobdefinition']
    jd_1_2 = admin.post('/api/v1/jobdefinitions',
                        data={'name': "pname2", 'priority': 0,
                              'test_id': t_id}).data['jobdefinition']
    jd_2_1 = admin.post('/api/v1/jobdefinitions',
                        data={'name': "pname3", 'priority': 1,
                              'test_id': t_id}).data['jobdefinition']
    jd_2_2 = admin.post('/api/v1/jobdefinitions',
                        data={'name': "pname3", 'priority': 1,
                              'test_id': t_id}).data['jobdefinition']

    jds = admin.get('/api/v1/jobdefinitions?sort=created_at').data
    assert jds['jobdefinitions'] == [jd_1_1, jd_1_2, jd_2_1, jd_2_2]

    # sort by priority first and then reverse by created_at
    jds = admin.get('/api/v1/jobdefinitions?sort=priority,-created_at').data
    assert jds['jobdefinitions'] == [jd_1_2, jd_1_1, jd_2_2, jd_2_1]


def test_get_jobdefinition_with_embed(admin, t_id):
    pt = admin.get('/api/v1/tests/%s' % t_id).data
    pjd = admin.post('/api/v1/jobdefinitions', data={'name': 'pname',
                     'test_id': t_id}).data
    del pjd['jobdefinition']['test_id']
    pjd['jobdefinition'][u'test'] = pt['test']

    # verify embed
    jd_embed = admin.get('/api/v1/jobdefinitions/pname?embed=test').data
    assert pjd == jd_embed


def test_get_jobdefinition_with_embed_not_valid(admin, t_id):
    admin.post('/api/v1/jobdefinitions', data={'name': 'pname',
               'test_id': t_id})

    # verify embed
    jds = admin.get('/api/v1/jobdefinitions/pname?embed=mdr')
    assert jds.status_code == 400


def test_delete_jobdefinition_not_found(admin):
    result = admin.delete('/api/v1/jobdefinitions/ptdr',
                          headers={'If-match': 'mdr'})
    assert result.status_code == 404
