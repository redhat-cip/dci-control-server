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


def test_get_identity_admin(admin, team_admin_id):
    response = admin.get('/api/v1/identity')
    assert response.status_code == 200
    assert 'identity' in response.data
    identity = response.data['identity']
    assert team_admin_id in identity['teams']
    assert identity['teams'][team_admin_id]['name'] == 'admin'
    assert identity['teams'][team_admin_id]['id'] == team_admin_id


def test_get_identity_unauthorized(unauthorized):
    response = unauthorized.get('/api/v1/identity')
    assert response.status_code == 401


def test_get_identity_user(user, team_user_id):
    response = user.get('/api/v1/identity')
    assert response.status_code == 200
    assert 'identity' in response.data
    identity = response.data['identity']
    assert identity['name'] == 'user'
    assert identity['teams'][team_user_id]['name'] == 'user'
    assert identity['teams'][team_user_id]['id'] == team_user_id


def get_user(flask_user, name):
    get = flask_user.get('/api/v1/users?where=name:%s' % name)
    get2 = flask_user.get('/api/v1/users/%s' % get.data['users'][0]['id'])
    return get2.data['user'], get2.headers.get("ETag")


def test_update_identity_password(admin, user):
    user_data, user_etag = get_user(admin, 'user')

    assert user.get('/api/v1/identity').status_code == 200

    assert user.put(
        '/api/v1/identity',
        data={'current_password': 'user', 'new_password': 'password'},
        headers={'If-match': user_etag}
    ).status_code == 200

    assert user.get('/api/v1/identity').status_code == 401

    user_data, user_etag = get_user(admin, 'user')

    assert admin.put(
        '/api/v1/users/%s' % user_data['id'],
        data={'password': 'user'},
        headers={'If-match': user_etag}
    ).status_code == 200

    assert user.get('/api/v1/identity').status_code == 200


def test_update_current_user_current_password_wrong(admin, user):
    user_data, user_etag = get_user(admin, 'user')

    assert user.get('/api/v1/identity').status_code == 200

    assert user.put(
        '/api/v1/identity',
        data={'current_password': 'wrong_password', 'new_password': ''},
        headers={'If-match': user_etag}
    ).status_code == 400

    assert user.get('/api/v1/identity').status_code == 200


def test_update_current_user_new_password_empty(admin, user):
    user_data, user_etag = get_user(admin, 'user')

    assert user.get('/api/v1/identity').status_code == 200

    assert user.put(
        '/api/v1/identity',
        data={'current_password': 'user', 'new_password': ''},
        headers={'If-match': user_etag}
    ).status_code == 200

    assert user.get('/api/v1/identity').status_code == 200


def test_update_current_user(admin, user):
    user_data, user_etag = get_user(admin, 'user')

    assert user.get('/api/v1/identity').status_code == 200

    me = user.put(
        '/api/v1/identity',
        data={'current_password': 'user', 'new_password': '',
              'email': 'new_email@example.org', 'fullname': 'New Name',
              'timezone': 'Europe/Paris'},
        headers={'If-match': user_etag}
    )
    assert me.status_code == 200
    assert me.data['user']['email'] == 'new_email@example.org'
    assert me.data['user']['fullname'] == 'New Name'
    assert me.data['user']['timezone'] == 'Europe/Paris'


def test_update_current_user_sso(rh_employee, app, admin):
    assert rh_employee.get('/api/v1/identity').status_code == 200
    user_data, user_etag = get_user(admin, 'rh_employee')
    me = rh_employee.put(
        '/api/v1/identity',
        data={
            'email': 'new_email@example.org',
            'fullname': 'New Name',
            'timezone': 'Europe/Paris'
        },
        headers={'If-match': user_etag}
    )
    assert me.status_code == 200
    assert me.data['user']['email'] == 'new_email@example.org'
    assert me.data['user']['fullname'] == 'New Name'
    assert me.data['user']['timezone'] == 'Europe/Paris'
