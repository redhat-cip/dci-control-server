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
import pytest


def test_create_remotecis(admin, team_id):
    pr = admin.post('/api/v1/remotecis',
                    data={'name': 'pname', 'team_id': team_id}).data
    pr_id = pr['remoteci']['id']
    gr = admin.get('/api/v1/remotecis/%s' % pr_id).data
    assert gr['remoteci']['name'] == 'pname'


def test_create_remotecis_already_exist(admin, team_id):
    pstatus_code = admin.post('/api/v1/remotecis',
                              data={'name': 'pname',
                                    'team_id': team_id}).status_code
    assert pstatus_code == 201

    pstatus_code = admin.post('/api/v1/remotecis',
                              data={'name': 'pname',
                                    'team_id': team_id}).status_code
    assert pstatus_code == 422


def test_get_all_remotecis(admin, team_id):
    remoteci_1 = admin.post('/api/v1/remotecis',
                            data={'name': 'pname1', 'team_id': team_id}).data
    remoteci_2 = admin.post('/api/v1/remotecis',
                            data={'name': 'pname2', 'team_id': team_id}).data

    db_all_remotecis = admin.get('/api/v1/remotecis?sort=created_at').data
    db_all_remotecis = db_all_remotecis['remotecis']
    db_all_remotecis_ids = [db_t['id'] for db_t in db_all_remotecis]

    assert db_all_remotecis_ids == [remoteci_1['remoteci']['id'],
                                    remoteci_2['remoteci']['id']]


def test_get_all_remotecis_with_where(admin, team_id):
    pr = admin.post('/api/v1/remotecis', data={'name': 'pname1',
                                               'team_id': team_id}).data
    pr_id = pr['remoteci']['id']

    db_r = admin.get('/api/v1/remotecis?where=id:%s' % pr_id).data
    db_r_id = db_r['remotecis'][0]['id']
    assert db_r_id == pr_id

    db_r = admin.get('/api/v1/remotecis?where=name:pname1').data
    db_r_id = db_r['remotecis'][0]['id']
    assert db_r_id == pr_id


def test_get_all_remotecis_with_pagination(admin, team_id):
    # create 4 components types and check meta data count
    admin.post('/api/v1/remotecis', data={'name': 'pname1',
                                          'team_id': team_id})
    admin.post('/api/v1/remotecis', data={'name': 'pname2',
                                          'team_id': team_id})
    admin.post('/api/v1/remotecis', data={'name': 'pname3',
                                          'team_id': team_id})
    admin.post('/api/v1/remotecis', data={'name': 'pname4',
                                          'team_id': team_id})
    remotecis = admin.get('/api/v1/remotecis').data
    assert remotecis['_meta']['count'] == 4

    # verify limit and offset are working well
    remotecis = admin.get('/api/v1/remotecis?limit=2&offset=0').data
    assert len(remotecis['remotecis']) == 2

    remotecis = admin.get('/api/v1/remotecis?limit=2&offset=2').data
    assert len(remotecis['remotecis']) == 2

    # if offset is out of bound, the api returns an empty list
    remotecis = admin.get('/api/v1/remotecis?limit=5&offset=300')
    assert remotecis.status_code == 200
    assert remotecis.data['remotecis'] == []


def test_get_all_remotecis_with_sort(admin, team_id):
    # create 2 remotecis ordered by created time
    r_1 = admin.post('/api/v1/remotecis',
                     data={'name': 'pname1',
                           'team_id': team_id}).data['remoteci']
    r_2 = admin.post('/api/v1/remotecis',
                     data={'name': 'pname2',
                           'team_id': team_id}).data['remoteci']

    grs = admin.get('/api/v1/remotecis?sort=created_at').data
    assert grs['remotecis'] == [r_1, r_2]

    # test in reverse order
    grs = admin.get('/api/v1/remotecis?sort=-created_at').data
    assert grs['remotecis'] == [r_2, r_1]


def test_get_all_remotecis_embed(admin, team_id):
    team = admin.get('/api/v1/teams/%s' % team_id).data['team']
    # create 2 remotecis
    admin.post('/api/v1/remotecis',
               data={'name': 'pname1', 'team_id': team_id})
    admin.post('/api/v1/remotecis',
               data={'name': 'pname2', 'team_id': team_id})

    # verify embed
    remotecis = admin.get('/api/v1/remotecis?embed=team').data

    for remoteci in remotecis['remotecis']:
        assert 'team_id' not in remoteci
        assert remoteci['team'] == team


def test_get_remoteci_by_id_or_name(admin, team_id):
    pr = admin.post('/api/v1/remotecis',
                    data={'name': 'pname', 'team_id': team_id}).data
    pr_id = pr['remoteci']['id']

    # get by uuid
    created_r = admin.get('/api/v1/remotecis/%s' % pr_id)
    assert created_r.status_code == 200

    created_r = created_r.data
    assert created_r['remoteci']['id'] == pr_id

    # get by name
    created_r = admin.get('/api/v1/remotecis/pname')
    assert created_r.status_code == 200

    created_r = created_r.data
    assert created_r['remoteci']['id'] == pr_id


def test_get_remoteci_with_embed(admin, team_id):
    team = admin.get('/api/v1/teams/%s' % team_id).data['team']
    premoteci = admin.post('/api/v1/remotecis',
                           data={'name': 'pname1', 'team_id': team_id}).data
    r_id = premoteci['remoteci']['id']

    # verify embed
    db_remoteci = admin.get('/api/v1/remotecis/%s?embed=team' % r_id).data
    assert 'team_id' not in premoteci
    assert db_remoteci['remoteci']['team'] == team


def test_get_remoteci_not_found(admin):
    result = admin.get('/api/v1/remotecis/ptdr')
    assert result.status_code == 404


def test_put_remotecis(admin, team_id):
    pr = admin.post('/api/v1/remotecis', data={'name': 'pname',
                                               'team_id': team_id})
    assert pr.status_code == 201

    pr_etag = pr.headers.get("ETag")

    gr = admin.get('/api/v1/remotecis/pname')
    assert gr.status_code == 200

    ppr = admin.put('/api/v1/remotecis/pname',
                    data={'name': 'nname'},
                    headers={'If-match': pr_etag})
    assert ppr.status_code == 204

    gr = admin.get('/api/v1/remotecis/pname')
    assert gr.status_code == 404

    gr = admin.get('/api/v1/remotecis/nname')
    assert gr.status_code == 200


def test_delete_remoteci_by_id(admin, team_id):
    pr = admin.post('/api/v1/remotecis',
                    data={'name': 'pname', 'team_id': team_id})
    pr_etag = pr.headers.get("ETag")
    pr_id = pr.data['remoteci']['id']
    assert pr.status_code == 201

    created_r = admin.get('/api/v1/remotecis/%s' % pr_id)
    assert created_r.status_code == 200

    deleted_r = admin.delete('/api/v1/remotecis/%s' % pr_id,
                             headers={'If-match': pr_etag})
    assert deleted_r.status_code == 204

    gr = admin.get('/api/v1/remotecis/%s' % pr_id)
    assert gr.status_code == 404


def test_delete_remoteci_not_found(admin):
    result = admin.delete('/api/v1/remotecis/ptdr',
                          headers={'If-match': 'mdr'})
    assert result.status_code == 404


# Tests for the isolation

def test_create_remoteci_as_user(user, team_user_id, team_id):
    remoteci = user.post('/api/v1/remotecis',
                         data={'name': 'rname', 'team_id': team_id})
    assert remoteci.status_code == 401

    remoteci = user.post('/api/v1/remotecis',
                         data={'name': 'rname', 'team_id': team_user_id})
    assert remoteci.status_code == 201


@pytest.mark.usefixtures('remoteci_id', 'remoteci_user_id')
def test_get_all_remotecis_as_user(user, team_user_id):
    remotecis = user.get('/api/v1/remotecis')
    assert remotecis.status_code == 200
    assert remotecis.data['_meta']['count'] == 1
    for remoteci in remotecis.data['remotecis']:
        assert remoteci['team_id'] == team_user_id


def test_get_remoteci_as_user(user, team_user_id, remoteci_id):
    remoteci = user.get('/api/v1/remotecis/%s' % remoteci_id)
    assert remoteci.status_code == 404

    user.post('/api/v1/remotecis',
              data={'name': 'rname', 'team_id': team_user_id})
    remoteci = user.get('/api/v1/remotecis/rname')
    assert remoteci.status_code == 200


def test_put_remoteci_as_user(user, team_user_id, remoteci_id, admin):
    user.post('/api/v1/remotecis',
              data={'name': 'rname', 'team_id': team_user_id})
    remoteci = user.get('/api/v1/remotecis/rname')
    remoteci_etag = remoteci.headers.get("ETag")

    remoteci_put = user.put('/api/v1/remotecis/rname',
                            data={'name': 'nname'},
                            headers={'If-match': remoteci_etag})
    assert remoteci_put.status_code == 204

    remoteci = admin.get('/api/v1/remotecis/%s' % remoteci_id)
    remoteci_etag = remoteci.headers.get("ETag")
    remoteci_put = user.put('/api/v1/remotecis/%s' % remoteci_id,
                            data={'name': 'nname'},
                            headers={'If-match': remoteci_etag})
    assert remoteci_put.status_code == 401


def test_delete_remoteci_as_user(user, team_user_id, admin, remoteci_id):
    user.post('/api/v1/remotecis',
              data={'name': 'rname', 'team_id': team_user_id})
    remoteci = user.get('/api/v1/remotecis/rname')
    remoteci_etag = remoteci.headers.get("ETag")

    remoteci_delete = user.delete('/api/v1/remotecis/rname',
                                  headers={'If-match': remoteci_etag})
    assert remoteci_delete.status_code == 204

    remoteci = admin.get('/api/v1/remotecis/%s' % remoteci_id)
    remoteci_etag = remoteci.headers.get("ETag")
    remoteci_delete = user.delete('/api/v1/remotecis/%s' % remoteci_id,
                                  headers={'If-match': remoteci_etag})
    assert remoteci_delete.status_code == 401
