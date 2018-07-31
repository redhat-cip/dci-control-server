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


def test_get_identity_admin(admin):
    response = admin.get('/api/v1/identity')
    assert response.status_code == 200
    assert 'identity' in response.data
    identity = response.data['identity']
    assert identity['name'] == 'admin'
    assert identity['team_name'] == 'admin'
    assert identity['role_label'] == 'SUPER_ADMIN'


def test_get_identity_unauthorized(unauthorized):
    response = unauthorized.get('/api/v1/identity')
    assert response.status_code == 401


def test_get_identity_user(user):
    response = user.get('/api/v1/identity')
    assert response.status_code == 200
    assert 'identity' in response.data
    identity = response.data['identity']
    assert identity['name'] == 'user'
    assert identity['team_name'] == 'user'
    assert identity['role_label'] == 'USER'
