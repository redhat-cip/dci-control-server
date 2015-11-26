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


def test_create_users(admin, team_id):
    pu = admin.post('/api/v1/users',
                    data={'name': 'pname', 'password': 'ppass',
                          'team_id': team_id}).data

    pu_id = pu['user']['id']
    gu = admin.get('/api/v1/users/%s' % pu_id).data
    assert gu['user']['name'] == 'pname'


def test_create_users_already_exist(admin, team_id):
    pstatus_code = admin.post('/api/v1/users',
                              data={'name': 'pname',
                                    'password': 'ppass',
                                    'team_id': team_id}).status_code
    assert pstatus_code == 201

    pstatus_code = admin.post('/api/v1/users',
                              data={'name': 'pname',
                                    'password': 'ppass',
                                    'team_id': team_id}).status_code
    assert pstatus_code == 400


def test_get_all_users(admin, team_id):
    # TODO(yassine): Currently there is already 3 users created in the DB,
    # this will be fixed later.
    db_users = admin.get('/api/v1/users?sort=created_at').data
    db_users = db_users['users']
    db_users_ids = [db_t['id'] for db_t in db_users]

    user_1 = admin.post('/api/v1/users', data={'name': 'pname1',
                                               'password': 'ppass',
                                               'team_id': team_id}).data
    user_2 = admin.post('/api/v1/users', data={'name': 'pname2',
                                               'password': 'ppass',
                                               'team_id': team_id}).data
    db_users_ids.extend([user_1['user']['id'], user_2['user']['id']])

    db_all_users = admin.get('/api/v1/users?sort=created_at').data
    db_all_users = db_all_users['users']
    db_all_users_ids = [db_t['id'] for db_t in db_all_users]

    assert db_all_users_ids == db_users_ids


def test_get_all_users_with_where(admin, team_id):
    pu = admin.post('/api/v1/users', data={'name': 'pname1',
                                           'password': 'ppass',
                                           'team_id': team_id}).data
    pu_id = pu['user']['id']

    db_u = admin.get('/api/v1/users?where=id:%s' % pu_id).data
    db_u_id = db_u['users'][0]['id']
    assert db_u_id == pu_id

    db_u = admin.get('/api/v1/users?where=name:pname1').data
    db_u_id = db_u['users'][0]['id']
    assert db_u_id == pu_id


def test_get_all_users_with_pagination(admin, team_id):
    # create 4 components types and check meta data count
    admin.post('/api/v1/users', data={'name': 'pname1',
                                      'password': 'ppass',
                                      'team_id': team_id})
    admin.post('/api/v1/users', data={'name': 'pname2',
                                      'password': 'ppass',
                                      'team_id': team_id})
    admin.post('/api/v1/users', data={'name': 'pname3',
                                      'password': 'ppass',
                                      'team_id': team_id})
    admin.post('/api/v1/users', data={'name': 'pname4',
                                      'password': 'ppass',
                                      'team_id': team_id})
    users = admin.get('/api/v1/users').data
    assert users['_meta']['count'] == 9

    # verify limit and offset are working well
    users = admin.get('/api/v1/users?limit=2&offset=0').data
    assert len(users['users']) == 2

    users = admin.get('/api/v1/users?limit=2&offset=2').data
    assert len(users['users']) == 2

    # if offset is out of bound, the api returns an empty list
    users = admin.get('/api/v1/users?limit=5&offset=300')
    assert users.status_code == 200
    assert users.data['users'] == []


def test_get_all_users_with_sort(admin, team_id):
    # TODO(yassine): Currently there is already 3 users created in the DB,
    # this will be fixed later.
    db_users = admin.get('/api/v1/users?sort=created_at').data
    db_users = db_users['users']

    # create 2 users ordered by created time
    user_1 = admin.post('/api/v1/users',
                        data={'name': 'pname1',
                              'password': 'ppass',
                              'role': 'user',
                              'team_id': team_id}).data['user']
    user_2 = admin.post('/api/v1/users',
                        data={'name': 'pname2',
                              'password': 'ppass',
                              'role': 'user',
                              'team_id': team_id}).data['user']

    gusers = admin.get('/api/v1/users?sort=created_at').data
    db_users.extend([user_1, user_2])
    assert gusers['users'] == db_users

    # test in reverse order
    db_users.reverse()
    gusers = admin.get('/api/v1/users?sort=-created_at').data
    assert gusers['users'] == db_users


def test_get_user_by_id_or_name(admin, team_id):
    puser = admin.post('/api/v1/users',
                       data={'name': 'pname',
                             'password': 'ppass',
                             'team_id': team_id}).data
    puser_id = puser['user']['id']

    # get by uuid
    created_user = admin.get('/api/v1/users/%s' % puser_id)
    assert created_user.status_code == 200

    created_user = created_user.data
    assert created_user['user']['id'] == puser_id

    # get by name
    created_user = admin.get('/api/v1/users/pname')
    assert created_user.status_code == 200

    created_user = created_user.data
    assert created_user['user']['id'] == puser_id


def test_get_user_not_found(admin):
    result = admin.get('/api/v1/users/ptdr')
    assert result.status_code == 404


def test_put_users(admin, team_id):
    pu = admin.post('/api/v1/users', data={'name': 'pname',
                                           'password': 'ppass',
                                           'team_id': team_id})
    assert pu.status_code == 201

    pu_etag = pu.headers.get("ETag")

    gu = admin.get('/api/v1/users/pname')
    assert gu.status_code == 200

    ppu = admin.put('/api/v1/users/pname',
                    data={'name': 'nname'},
                    headers={'If-match': pu_etag})
    assert ppu.status_code == 204

    gu = admin.get('/api/v1/users/pname')
    assert gu.status_code == 404

    gu = admin.get('/api/v1/users/nname')
    assert gu.status_code == 200


def test_delete_user_by_id(admin, team_id):
    pu = admin.post('/api/v1/users',
                    data={'name': 'pname',
                          'password': 'ppass',
                          'team_id': team_id})
    pu_etag = pu.headers.get("ETag")
    pu_id = pu.data['user']['id']
    assert pu.status_code == 201

    created_user = admin.get('/api/v1/users/%s' % pu_id)
    assert created_user.status_code == 200

    deleted_user = admin.delete('/api/v1/users/%s' % pu_id,
                                headers={'If-match': pu_etag})
    assert deleted_user.status_code == 204

    gu = admin.get('/api/v1/users/%s' % pu_id)
    assert gu.status_code == 404


def test_delete_user_not_found(admin):
    result = admin.delete('/api/v1/users/ptdr',
                          headers={'If-match': 'mdr'})
    assert result.status_code == 404


# Tests for the isolation

def test_create_user_as_user(user, user_admin, team_user_id):
    # simple user cannot add a new user to its team
    pu = user.post('/api/v1/users',
                   data={'name': 'pname',
                         'password': 'ppass',
                         'team_id': team_user_id})
    assert pu.status_code == 401

    # admin user can add a new user to its team
    pu = user_admin.post('/api/v1/users',
                         data={'name': 'pname',
                               'password': 'ppass',
                               'team_id': team_user_id})
    assert pu.status_code == 201


def test_get_all_users_as_user(user, team_user_id):
    users = user.get('/api/v1/users')
    assert users.status_code == 200
    for guser in users.data['users']:
        assert guser['team_id'] == team_user_id


def test_get_user_as_user(user):
    # admin does not belong to this user's team
    guser = user.get('/api/v1/users/admin')
    assert guser.status_code == 404

    guser = user.get('/api/v1/users/user')
    assert guser.status_code == 200


# Only super admin and an admin of a team can update the user
def test_put_user_as_user_admin(user, user_admin):
    puser = user.get('/api/v1/users/user')
    user_etag = puser.headers.get("ETag")

    user_put = user.put('/api/v1/users/user_admin',
                        data={'name': 'nname'},
                        headers={'If-match': user_etag})
    assert user_put.status_code == 401

    user_put = user_admin.put('/api/v1/users/user',
                              data={'name': 'nname'},
                              headers={'If-match': user_etag})
    assert user_put.status_code == 204


# Only super admin can delete a team
def test_delete_as_user_admin(user, user_admin):
    puser = user.get('/api/v1/users/user')
    user_etag = puser.headers.get("ETag")

    user_delete = user.delete('/api/v1/users/user',
                              headers={'If-match': user_etag})
    assert user_delete.status_code == 401

    user_delete = user_admin.delete('/api/v1/users/user',
                                    headers={'If-match': user_etag})
    assert user_delete.status_code == 204
