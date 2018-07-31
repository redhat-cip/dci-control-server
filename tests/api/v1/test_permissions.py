# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Red Hat, Inc
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


def test_success_create_permission(admin):
    data = {
        'name': 'A Permission',
        'label': 'APERMISSION',
        'description': 'This is a regular permissions',
    }

    result = admin.post('/api/v1/permissions', data=data)

    assert result.status_code == 201
    assert result.data['permission']['name'] == data['name']
    assert result.data['permission']['label'] == data['label']
    assert result.data['permission']['description'] == data['description']


def test_fail_create_permission_user_admin(user_admin):
    data = {
        'name': 'A Permission',
        'label': 'APERMISSION',
        'description': 'This is a regular permissions',
    }

    result = user_admin.post('/api/v1/permissions', data=data)

    assert result.status_code == 401


def test_fail_create_permission_user(user):
    data = {
        'name': 'A Permission',
        'label': 'APERMISSION',
        'description': 'This is a regular permissions',
    }

    result = user.post('/api/v1/permissions', data=data)

    assert result.status_code == 401


def test_fail_ensure_payload_content_is_checked(admin):
    data = {
        'description': 'This is a regular permissions',
    }

    result = admin.post('/api/v1/permissions', data=data)

    assert result.status_code == 400


def test_fail_create_permission_already_exists(admin):
    data = {
        'name': 'A Permission',
        'label': 'APERMISSION',
        'description': 'This is a regular permissions',
    }

    result = admin.post('/api/v1/permissions', data=data)
    assert result.status_code == 201
    result = admin.post('/api/v1/permissions', data=data)
    assert result.status_code == 409


def test_success_update_permission(admin, permission):
    permission_id = permission['id']

    url = '/api/v1/permissions/%s' % permission_id
    assert permission['name'] == 'A Permission'

    result = admin.put(url, data={'name': 'New Permission'},
                       headers={'If-match': permission['etag']})
    assert result.status_code == 200
    assert result.data['permission']['name'] == 'New Permission'
    assert result.data['permission']['description'] == \
        'This is a regular permission'

    result = admin.put(url, data={'description': 'new permission'},
                       headers={'If-match': result.data['permission']['etag']})
    assert result.status_code == 200
    assert result.data['permission']['name'] == 'New Permission'
    assert result.data['permission']['description'] == 'new permission'


def test_success_get_all_permissions_admin(admin, permission):
    result = admin.get('/api/v1/permissions')

    assert result.status_code == 200

    permissions = [r['label'] for r in result.data['permissions']]
    assert ['APERMISSION'] == sorted(permissions)


def test_success_get_all_permissions_user_admin(user_admin, permission):
    result = user_admin.get('/api/v1/permissions')

    assert result.status_code == 200

    permissions = [r['label'] for r in result.data['permissions']]
    assert ['APERMISSION'] == sorted(permissions)


def test_success_get_all_permissions_user(user, permission):
    result = user.get('/api/v1/permissions')

    assert result.status_code == 200

    permissions = [r['label'] for r in result.data['permissions']]
    assert ['APERMISSION'] == sorted(permissions)


def test_success_delete_permission_admin(admin, permission):
    result = admin.delete('/api/v1/permissions/%s' % permission['id'],
                          headers={'If-match': permission['etag']})

    assert result.status_code == 204

    result = admin.get('/api/v1/permissions')
    assert len(result.data['permissions']) == 0

    result = admin.get('/api/v1/permissions/purge')
    assert len(result.data['permissions']) == 1


def test_fail_delete_permission_user_admin(user_admin, permission):
    result = user_admin.delete('/api/v1/permissions/%s' % permission['id'],
                               headers={'If-match': permission['etag']})

    assert result.status_code == 401


def test_fail_delete_permission_user(user, permission):
    result = user.delete('/api/v1/permissions/%s' % permission['id'],
                         headers={'If-match': permission['etag']})

    assert result.status_code == 401
