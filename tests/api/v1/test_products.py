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


def test_success_create_product(admin, team_id):
    data = {
        'name': 'OpenStack',
        'label': 'OPENSTACK',
        'description': 'Red Hat OpenStack Platform',
        'team_id': team_id
    }

    result = admin.post('/api/v1/products', data=data)

    assert result.status_code == 201
    assert result.data['product']['name'] == data['name']
    assert result.data['product']['label'] == data['label']
    assert result.data['product']['description'] == data['description']
    assert result.data['product']['team_id'] == data['team_id']


def test_fail_create_permission_user(user, team_id):
    data = {
        'name': 'OpenStack',
        'label': 'OPENSTACK',
        'description': 'Red Hat OpenStack Platform',
        'team_id': team_id
    }

    result = user.post('/api/v1/products', data=data)

    assert result.status_code == 401


def test_fail_ensure_payload_content_is_checked(admin):
    data = {
        'description': 'name and team_id are missing',
    }

    result = admin.post('/api/v1/products', data=data)

    assert result.status_code == 400


def test_fail_create_product_already_exists(admin, team_id):
    data = {
        'name': 'OpenStack',
        'label': 'OPENSTACK',
        'description': 'Red Hat OpenStack Platform',
        'team_id': team_id
    }

    result = admin.post('/api/v1/products', data=data)
    assert result.status_code == 201
    result = admin.post('/api/v1/products', data=data)
    assert result.status_code == 409


def test_success_update_product(admin, product):
    product_id = product['id']

    url = '/api/v1/products/%s' % product_id
    assert product['name'] == 'OpenStack'

    result = admin.put(url, data={'name': 'New OpenStack'},
                       headers={'If-match': product['etag']})
    assert result.status_code == 204

    product = admin.get(url).data
    assert product['product']['name'] == 'New OpenStack'
    assert product['product']['description'] == \
        'Red Hat OpenStack Platform'

    result = admin.put(url, data={'description': 'new product'},
                       headers={'If-match': product['product']['etag']})
    assert result.status_code == 204

    product = admin.get(url).data
    assert product['product']['name'] == 'New OpenStack'
    assert product['product']['description'] == 'new product'


def test_fail_update_product_unauthorized_fields(admin, product):
    label = {
        'label': 'NEW LABEL',
    }

    result = admin.put('/api/v1/products/%s' % product['id'], data=label,
                       headers={'If-match': product['etag']})

    assert result.status_code == 400


def test_success_get_all_products_admin(admin, product):
    result = admin.get('/api/v1/products')

    assert result.status_code == 200

    products = [r['label'] for r in result.data['products']]
    assert ['OPENSTACK'] == sorted(products)


def test_success_delete_product_admin(admin, product):
    result = admin.delete('/api/v1/products/%s' % product['id'],
                          headers={'If-match': product['etag']})

    assert result.status_code == 204

    result = admin.get('/api/v1/products')
    assert len(result.data['products']) == 0

    result = admin.get('/api/v1/products/purge')
    assert len(result.data['products']) == 1


def test_fail_delete_product_user_admin(user_admin, product):
    result = user_admin.delete('/api/v1/products/%s' % product['id'],
                               headers={'If-match': product['etag']})

    assert result.status_code == 401


def test_fail_delete_product_user(user, product):
    result = user.delete('/api/v1/products/%s' % product['id'],
                         headers={'If-match': product['etag']})

    assert result.status_code == 401
