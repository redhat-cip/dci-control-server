# -*- coding: utf-8 -*-
#
# Copyright (C) 2017-2018 Red Hat, Inc
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


def test_create_fingerprint(admin, topic_id):
    values = {'name': 'pname',
              'topic_id': topic_id,
              'fingerprint': {'regexp': '.*'},
              'actions': {'meta': 'test'},
              'description': 'test'}
    fp = admin.post('/api/v1/fingerprints', data=values).data
    fp_id = fp['fingerprint']['id']
    gfp = admin.get('/api/v1/fingerprints/%s' % fp_id).data
    assert gfp['fingerprint']['name'] == 'pname'


def test_get_all_fingerprints(admin, topic_id):
    values = {'name': 'pname1',
              'topic_id': topic_id,
              'fingerprint': {'regexp': '.*'},
              'actions': {'meta': 'test'},
              'description': 'test'}
    db_fp_1 = admin.post('/api/v1/fingerprints', data=values).data
    values['name'] = 'pname2'
    db_fp_2 = admin.post('/api/v1/fingerprints', data=values).data
    values['name'] = 'pname3'
    db_fp_3 = admin.post('/api/v1/fingerprints', data=values).data
    db_fp_post_ids = [db_fp_1['fingerprint']['id'],
                      db_fp_2['fingerprint']['id'],
                      db_fp_3['fingerprint']['id']]

    db_fp = admin.get('/api/v1/fingerprints?sort=created_at').data
    db_fp = db_fp['fingerprints']
    db_fp_ids = [db_fpl['id'] for db_fpl in db_fp]

    assert db_fp_post_ids == db_fp_ids


def test_put_fingerprint(admin, topic_id):
    values = {'name': 'pname1',
              'topic_id': topic_id,
              'fingerprint': {'regexp': '.*'},
              'actions': {'meta': 'test'},
              'description': 'test'}
    fp = admin.post('/api/v1/fingerprints', data=values)
    assert fp.status_code == 201

    fp_etag = fp.headers.get("ETag")

    gfp = admin.get('/api/v1/fingerprints/%s' % fp.data['fingerprint']['id'])
    assert gfp.status_code == 200

    pfp = admin.put('/api/v1/fingerprints/%s' % gfp.data['fingerprint']['id'],
                    data={'name': 'nname'},
                    headers={'If-match': fp_etag})
    assert pfp.status_code == 200
    assert pfp.data['fingerprint']['name'] == 'nname'


def test_delete_fingerprint_by_id(admin, topic_id):
    values = {'name': 'pname1',
              'topic_id': topic_id,
              'fingerprint': {'regexp': '.*'},
              'actions': {'meta': 'test'},
              'description': 'test'}
    fp = admin.post('/api/v1/fingerprints',
                    data=values)
    fp_etag = fp.headers.get("ETag")
    fp_id = fp.data['fingerprint']['id']
    assert fp.status_code == 201

    created_t = admin.get('/api/v1/fingerprints/%s' % fp_id)
    assert created_t.status_code == 200

    deleted_t = admin.delete('/api/v1/fingerprints/%s' % fp_id,
                             headers={'If-match': fp_etag})
    assert deleted_t.status_code == 204

    gfp = admin.get('/api/v1/fingerprints/%s' % fp_id)
    assert gfp.status_code == 404
