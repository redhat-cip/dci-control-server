# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Red Hat, Inc
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


def test_success_create_role_admin(admin):
    data = {
        'name': 'Manager',
        'description': 'A Manager role',
    }

    result = admin.post('/api/v1/roles', data=data)

    assert result.status_code == 201
    assert result.data['role']['name'] == data['name']
    assert result.data['role']['description'] == data['description']


def test_fail_create_role_team_admin(user_admin):
    data = {
        'name': 'Manager',
        'description': 'A Manager role',
    }

    result = user_admin.post('/api/v1/roles', data=data)

    assert result.status_code == 401


def test_fail_create_role_user(user):
    data = {
        'name': 'Manager',
        'description': 'A Manager role',
    }

    result = user.post('/api/v1/roles', data=data)

    assert result.status_code == 401


def test_success_create_role_correct_payload(admin):
    data = {
        'name': 'Manager',
        'description': 'A Manager role',
    }

    result = admin.post('/api/v1/roles', data=data)

    assert result.status_code == 201


def test_fail_create_role_incorrect_payload(admin):
    data = {
        'description': 'A Manager role',
    }

    result = admin.post('/api/v1/roles', data=data)

    assert result.status_code == 400


def test_fail_create_role_already_exists(admin):
    data = {
        'name': 'Manager',
        'description': 'A Manager role',
    }

    result = admin.post('/api/v1/roles', data=data)
    assert result.status_code == 201
    result = admin.post('/api/v1/roles', data=data)
    assert result.status_code == 409


def test_success_update_role(admin, role):
    role_id = role['id']

    url = '/api/v1/roles/%s' % role_id
    assert role['name'] == 'Manager'

    result = admin.put(url, data={'name': 'Random Role'},
                       headers={'If-match': role['etag']})
    assert result.status_code == 204

    role = admin.get(url).data
    assert role['role']['name'] == 'Random Role'
    assert role['role']['description'] == 'A Manager role'

    result = admin.put(url, data={'description': 'new role'},
                       headers={'If-match': role['role']['etag']})
    assert result.status_code == 204

    role = admin.get(url).data
    assert role['role']['name'] == 'Random Role'
    assert role['role']['description'] == 'new role'


def test_fail_update_role_unauthorized_fields(admin, role):
    team_id = {
        'team_id': 'a265e652-dcbc-4d99-9f74-e60988250403',
    }

    result = admin.put('/api/v1/roles/%s' % role['id'], data=team_id,
                       headers={'If-match': role['etag']})

    assert result.status_code == 400


def test_success_get_role_by_id(admin, role):
    result = admin.get('/api/v1/roles/%s' % role['id'])

    assert result.status_code == 200
    assert result.data['role']['name'] == 'Manager'


def test_success_get_all_roles_admin(admin, role):
    result = admin.get('/api/v1/roles')

    assert result.status_code == 200
    assert len(result.data['roles']) == 4


def test_success_get_all_roles_user(user, role):
    result = user.get('/api/v1/roles')

    assert result.status_code == 200
    assert len(result.data['roles']) == 4


def test_success_delete_role_admin(admin, role):
    result = admin.delete('/api/v1/roles/%s' % role['id'],
                          headers={'If-match': role['etag']})

    assert result.status_code == 204

    result = admin.get('/api/v1/roles')

    assert len(result.data['roles']) == 3


def test_fail_delete_role_user(user, role):
    result = user.delete('/api/v1/roles/%s' % role['id'],
                         headers={'If-match': role['etag']})

    assert result.status_code == 401
