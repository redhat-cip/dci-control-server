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


def test_success_create_feeder_authorized_users(admin, epm,
                                                team_product_id):
    """Test to ensure user with proper permissions can create feeders

       Currently only the role SUPER_ADMIN and PRODUCT_OWNER have such
       a permission.
    """

    feeder_from_admin = {
        'name': 'feeder-from-admin', 'team_id': team_product_id
    }
    feeder_from_po = {
        'name': 'feeder-from-po', 'team_id': team_product_id
    }

    admin_result = admin.post('/api/v1/feeders', data=feeder_from_admin)
    epm_result = epm.post('/api/v1/feeders', data=feeder_from_po)

    assert admin_result.status_code == 201
    assert admin_result.data['feeder']['name'] == feeder_from_admin['name']

    assert epm_result.status_code == 201
    assert epm_result.data['feeder']['name'] == feeder_from_po['name']


def test_failure_create_feeder_unauthorized_users(user, team_product_id):
    """Test to ensure user w/o proper permissions can't create feeders

       Currently only the role SUPER_ADMIN and PRODUCT_OWNER have such
       a permission. So we test with a regular USER.
    """

    feeder_from_user = {
        'name': 'feeder-from-user', 'team_id': team_product_id
    }

    user_result = user.post('/api/v1/feeders', data=feeder_from_user)

    assert user_result.status_code == 401


def test_success_get_feeder_authorized_users(admin, epm, feeder):
    """Test to ensure user with proper permissions can retrieve feeders."""

    admin_result = admin.get('/api/v1/feeders')
    assert admin_result.data['_meta']['count'] == 1
    assert admin_result.data['feeders'][0]['name'] == 'random-name-feeder'

    epm_result = epm.get('/api/v1/feeders')
    assert epm_result.data['_meta']['count'] == 1
    assert epm_result.data['feeders'][0]['name'] == 'random-name-feeder'


def test_failure_get_feeder_unauthorized_users(user, feeder):
    """Test to ensure user w/o proper permissions can'tretrieve feeders."""

    user_result = user.get('/api/v1/feeders')
    assert user_result.status_code == 200
    assert user_result.data['feeders'] == []


def test_success_delete_feeder_authorized_users(admin, epm, feeder,
                                                team_product_id):
    """Test to ensure user with proper permissions can delete feeders."""

    feeder_from_po = {
        'name': 'feeder-from-po', 'team_id': team_product_id
    }

    epm_result = epm.post('/api/v1/feeders', data=feeder_from_po)
    feeder_from_po_id = epm_result.data['feeder']['id']
    feeder_from_po_etag = epm_result.headers.get("ETag")

    admin.delete('/api/v1/feeders/%s' % feeder['id'],
                 headers={'If-match': feeder['etag']})
    epm.delete('/api/v1/feeders/%s' % feeder_from_po_id,
                         headers={'If-match': feeder_from_po_etag})

    admin_retrieve = admin.get('/api/v1/feeders/%s' % feeder['id'])
    po_retrieve = epm.get('/api/v1/feeders/%s' % feeder_from_po_id)

    assert admin_retrieve.status_code == 404
    assert po_retrieve.status_code == 404


def test_failure_delete_feeder_unauthorized_users(user, feeder):
    """Test to ensure user w/o proper permissions can't delete feeders."""

    user_result = user.delete('/api/v1/feeders/%s' % feeder['id'],
                              headers={'If-match': feeder['etag']})
    assert user_result.status_code == 401


def test_success_put_feeder_authorized_users(admin, epm, feeder):
    """Test to ensure user with proper permissions can update feeders."""

    admin.put('/api/v1/feeders/%s' % feeder['id'], data={'name': 'newname'},
              headers={'If-match': feeder['etag']})

    admin_result = admin.get('/api/v1/feeders/%s' % feeder['id'])
    feeder_etag = admin_result.data['feeder']['etag']

    assert admin_result.data['feeder']['name'] == 'newname'

    epm.put('/api/v1/feeders/%s' % feeder['id'],
                      data={'name': 'newname-po'},
                      headers={'If-match': feeder_etag})

    epm_result = epm.get('/api/v1/feeders/%s' % feeder['id'])

    assert epm_result.data['feeder']['name'] == 'newname-po'


def test_failure_put_feeder_unauthorized_users(user, feeder):
    """Test to ensure user w/o proper permissions can't update feeders."""

    user_result = user.put('/api/v1/feeders/%s' % feeder['id'],
                           data={'name': 'newname'},
                           headers={'If-match': feeder['etag']})
    assert user_result.status_code == 401


def test_success_refresh_secret_feeder_authorized_users(admin, epm,
                                                        feeder):
    """Test to ensure user with proper permissions can update feeders."""

    original_api_secret = feeder['api_secret']
    admin.put('/api/v1/feeders/%s/api_secret' % feeder['id'],
              headers={'If-match': feeder['etag']})

    admin_result = admin.get('/api/v1/feeders/%s' % feeder['id'])
    feeder_etag = admin_result.data['feeder']['etag']

    assert admin_result.data['feeder']['api_secret']
    assert admin_result.data['feeder']['api_secret'] != original_api_secret

    original_api_secret = admin_result.data['feeder']['api_secret']
    epm.put('/api/v1/feeders/%s/api_secret' % feeder['id'],
                      headers={'If-match': feeder_etag})

    epm_result = epm.get('/api/v1/feeders/%s' % feeder['id'])

    assert epm_result.data['feeder']['api_secret']
    assert epm_result.data['feeder']['api_secret'] != original_api_secret


def test_failure_refresh_secret_feeder_unauthorized_users(user, feeder):
    """Test to ensure user w/o proper permissions can't update feeders."""

    user_result = user.put(
        '/api/v1/feeders/%s/api_secret' % feeder['id'],
        data={'name': 'newname'}, headers={'If-match': feeder['etag']}
    )
    assert user_result.status_code == 401


def test_success_ensure_put_api_secret_is_not_leaked(admin, feeder):
    """Test to ensure API secret is not leaked during update."""

    res = admin.put('/api/v1/feeders/%s' % feeder['id'],
                    data={'name': 'newname'},
                    headers={'If-match': feeder['etag']})

    assert res.status_code == 200
    assert 'api_secret' not in res.data['feeder']
