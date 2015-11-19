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


def test_create_remotecis(admin, team_id):
    pt = admin.post('/api/v1/remotecis',
                    data={'name': 'pname', 'team_id': team_id}).data
    pt_id = pt['remoteci']['id']
    gt = admin.get('/api/v1/remotecis/%s' % pt_id).data
    assert gt['remoteci']['name'] == 'pname'


def test_create_remotecis_already_exist(admin, team_id):
    pstatus_code = admin.post('/api/v1/remotecis',
                              data={'name': 'pname', 'team_id': team_id}).status_code
    assert pstatus_code == 201

    pstatus_code = admin.post('/api/v1/remotecis',
                              data={'name': 'pname'}).status_code
    assert pstatus_code == 400


def test_get_all_remotecis(admin, team_id):
    test_1 = admin.post('/api/v1/remotecis', data={'name': 'pname1', 'team_id': team_id}).data
    test_2 = admin.post('/api/v1/remotecis', data={'name': 'pname2', 'team_id': team_id}).data

    db_all_remotecis = admin.get('/api/v1/remotecis?sort=created_at').data
    db_all_remotecis = db_all_remotecis['remotecis']
    db_all_remotecis_ids = [db_t['id'] for db_t in db_all_remotecis]

    assert db_all_remotecis_ids == [test_1['remoteci']['id'],
                                    test_2['remoteci']['id']]


def test_get_all_remotecis_with_where(admin, team_id):
    pt = admin.post('/api/v1/remotecis', data={'name': 'pname1', 'team_id': team_id}).data
    pt_id = pt['remoteci']['id']

    db_t = admin.get('/api/v1/remotecis?where=id:%s' % pt_id).data
    db_t_id = db_t['remotecis'][0]['id']
    assert db_t_id == pt_id

    db_t = admin.get('/api/v1/remotecis?where=name:pname1').data
    db_t_id = db_t['remotecis'][0]['id']
    assert db_t_id == pt_id


def test_get_all_remotecis_with_pagination(admin, team_id):
    # create 4 components types and check meta data count
    admin.post('/api/v1/remotecis', data={'name': 'pname1', 'team_id': team_id})
    admin.post('/api/v1/remotecis', data={'name': 'pname2', 'team_id': team_id})
    admin.post('/api/v1/remotecis', data={'name': 'pname3', 'team_id': team_id})
    admin.post('/api/v1/remotecis', data={'name': 'pname4', 'team_id': team_id})
    ts = admin.get('/api/v1/remotecis').data
    assert ts['_meta']['count'] == 4

    # verify limit and offset are working well
    ts = admin.get('/api/v1/remotecis?limit=2&offset=0').data
    assert len(ts['remotecis']) == 2

    ts = admin.get('/api/v1/remotecis?limit=2&offset=2').data
    assert len(ts['remotecis']) == 2

    # if offset is out of bound, the api returns an empty list
    ts = admin.get('/api/v1/remotecis?limit=5&offset=300')
    assert ts.status_code == 200
    assert ts.data['remotecis'] == []


def test_get_all_remotecis_with_sort(admin, team_id):
    # create 2 remotecis ordered by created time
    t_1 = admin.post('/api/v1/remotecis',
                     data={'name': 'pname1', 'team_id': team_id}).data['remoteci']
    t_2 = admin.post('/api/v1/remotecis',
                     data={'name': 'pname2', 'team_id': team_id}).data['remoteci']

    gts = admin.get('/api/v1/remotecis?sort=created_at').data
    assert gts['remotecis'] == [t_1, t_2]

    # test in reverse order
    gts = admin.get('/api/v1/remotecis?sort=-created_at').data
    assert gts['remotecis'] == [t_2, t_1]


def test_get_remoteci_by_id_or_name(admin, team_id):
    pt = admin.post('/api/v1/remotecis',
                    data={'name': 'pname', 'team_id': team_id}).data
    pt_id = pt['remoteci']['id']

    # get by uuid
    created_t = admin.get('/api/v1/remotecis/%s' % pt_id)
    assert created_t.status_code == 200

    created_t = created_t.data
    assert created_t['remoteci']['id'] == pt_id

    # get by name
    created_t = admin.get('/api/v1/remotecis/pname')
    assert created_t.status_code == 200

    created_t = created_t.data
    assert created_t['remoteci']['id'] == pt_id


def test_get_remoteci_not_found(admin):
    result = admin.get('/api/v1/remotecis/ptdr')
    assert result.status_code == 404


def test_put_remotecis(admin, team_id):
    pt = admin.post('/api/v1/remotecis', data={'name': 'pname', 'team_id': team_id})
    assert pt.status_code == 201

    pt_etag = pt.headers.get("ETag")

    gt = admin.get('/api/v1/remotecis/pname')
    assert gt.status_code == 200

    ppt = admin.put('/api/v1/remotecis/pname',
                    data={'name': 'nname'},
                    headers={'If-match': pt_etag})
    assert ppt.status_code == 204

    gt = admin.get('/api/v1/remotecis/pname')
    assert gt.status_code == 404

    gt = admin.get('/api/v1/remotecis/nname')
    assert gt.status_code == 200


def test_delete_remoteci_by_id(admin, team_id):
    pt = admin.post('/api/v1/remotecis',
                    data={'name': 'pname', 'team_id': team_id})
    pt_etag = pt.headers.get("ETag")
    pt_id = pt.data['remoteci']['id']
    assert pt.status_code == 201

    created_t = admin.get('/api/v1/remotecis/%s' % pt_id)
    assert created_t.status_code == 200

    deleted_t = admin.delete('/api/v1/remotecis/%s' % pt_id,
                             headers={'If-match': pt_etag})
    assert deleted_t.status_code == 204

    gt = admin.get('/api/v1/remotecis/%s' % pt_id)
    assert gt.status_code == 404


def test_delete_remoteci_not_found(admin):
    result = admin.delete('/api/v1/remotecis/ptdr',
                          headers={'If-match': 'mdr'})
    assert result.status_code == 404
