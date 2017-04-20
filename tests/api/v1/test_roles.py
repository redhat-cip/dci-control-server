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
import pytest


def test_success_create_role_admin(admin):
    data = {
        'name': 'Manager',
        'description': 'A Manager role',
    }

    result = admin.post('/api/v1/roles', data=data)

    assert result.status_code == 201
    assert result.data['role']['name'] == data['name']
    assert result.data['role']['description'] == data['description']
    assert result.data['role']['team_id'] is not None


def test_success_create_role_team_admin(user_admin):
    data = {
        'name': 'Manager',
        'description': 'A Manager role',
    }

    result = user_admin.post('/api/v1/roles', data=data)

    assert result.status_code == 201
    assert result.data['role']['name'] == data['name']
    assert result.data['role']['description'] == data['description']
    assert result.data['role']['team_id'] is not None


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


def test_success_update_role_authorized_fields(admin, role):
    name = {
        'name': 'UpdatedManager',
    }

    description = {
        'description': 'UpdatedDescription',
    }

    result = admin.put('/api/v1/roles/%s' % role['id'], data=name,
                       headers={'If-match': role['etag']})
    role = admin.get('/api/v1/roles/%s' % role['id']).data

    assert result.status_code == 204
    assert role['role']['name'] == name['name']

    result = admin.put('/api/v1/roles/%s' % role['role']['id'],
                       data=description,
                       headers={'If-match': role['role']['etag']})
    role = admin.get('/api/v1/roles/%s' % role['role']['id']).data

    assert result.status_code == 204
    assert role['role']['description'] == description['description']


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


@pytest.mark.usefixtures('role', 'role_user_team',
                         'role_resu_team')
def test_success_get_all_roles_admin(admin):
    result = admin.get('/api/v1/roles')

    assert result.status_code == 200
    assert len(result.data['roles']) == 3


@pytest.mark.usefixtures('role', 'role_user_team',
                         'role_resu_team')
def test_sucess_get_all_roles_user(user_admin):
    result = user_admin.get('/api/v1/roles')

    assert result.status_code == 200
    assert len(result.data['roles']) == 2
    for role in result.data['roles']:
        if not role['system']:
            assert 'User Team' in role['name']


@pytest.mark.usefixtures('role', 'role_user_team',
                         'role_resu_team')
def test_sucess_get_all_roles_resu(resu_admin):
    result = resu_admin.get('/api/v1/roles')

    assert result.status_code == 200
    assert len(result.data['roles']) == 2
    for role in result.data['roles']:
        if not role['system']:
            assert 'Resu Team' in role['name']


def test_success_delete_role_admin(admin, role):
    result = admin.delete('/api/v1/roles/%s' % role['id'],
                          headers={'If-match': role['etag']})

    assert result.status_code == 204

    result = admin.get('/api/v1/roles')

    assert len(result.data['roles']) == 0


def test_success_delete_authorized_role_user_admin(user_admin,
                                                   role_user_team):
    role_id = role_user_team['id']
    result = user_admin.delete('/api/v1/roles/%s' % role_id,
                               headers={'If-match': role_user_team['etag']})

    assert result.status_code == 204

    result = user_admin.get('/api/v1/roles/%s' % role_id)

    assert result.status_code == 404


def test_fail_delete_unauthorized_role_user_admin(user_admin, role):
    result = user_admin.delete('/api/v1/roles/%s' % role['id'],
                               headers={'If-match': role['etag']})

    assert result.status_code == 401


def test_fail_delete_role_user(user, role_user_team):
    result = user.delete('/api/v1/roles/%s' % role_user_team['id'],
                         headers={'If-match': role_user_team['etag']})

    assert result.status_code == 401
