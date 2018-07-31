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


def test_create_meta(user, job_user_id):
    meta = user.post('/api/v1/jobs/%s/metas' % job_user_id,
                     data={'name': 'kikoo', 'value': 'lol'})
    assert meta.status_code == 201


def test_create_meta_without_value(user, job_user_id):
    meta = user.post('/api/v1/jobs/%s/metas' % job_user_id,
                     data={'name': 'kikoo'})
    assert meta.status_code == 201


def test_delete_meta(user, job_user_id):
    meta = user.post('/api/v1/jobs/%s/metas' % job_user_id,
                     data={'name': 'kikoo', 'value': 'lol'})
    meta_id = meta.data['meta']['id']
    assert meta.status_code == 201

    meta_deleted = user.delete('/api/v1/jobs/%s/metas/%s' % (job_user_id,
                                                             meta_id))
    assert meta_deleted.status_code == 204

    all_metas = user.get('/api/v1/jobs/%s/metas' % job_user_id).data
    assert not all_metas['metas']


def test_get_all_metas_from_job(user, job_user_id):
    meta_1 = user.post('/api/v1/jobs/%s/metas' % job_user_id,
                       data={'name': 'kikoo', 'value': 'lol'})
    assert meta_1.status_code == 201

    meta_2 = user.post('/api/v1/jobs/%s/metas' % job_user_id,
                       data={'name': 'kikoo2', 'value': 'lol2'})
    assert meta_2.status_code == 201

    all_metas = user.get('/api/v1/jobs/%s/metas' % job_user_id).data
    assert len(all_metas['metas']) == 2


def test_put_meta(user, job_user_id):
    meta = user.post('/api/v1/jobs/%s/metas' % job_user_id,
                     data={'name': 'kikoo', 'value': 'lol'})
    meta_id = meta.data['meta']['id']
    assert meta.status_code == 201
    meta_etag = meta.headers.get("ETag")

    meta_put = user.put('/api/v1/jobs/%s/metas/%s' % (job_user_id, meta_id),
                        data={'name': 'kikoo2', 'value': 'lol2'},
                        headers={'If-match': meta_etag})
    assert meta_put.status_code == 204

    all_metas = user.get('/api/v1/jobs/%s/metas' % job_user_id).data
    assert all_metas['metas']
    assert all_metas['metas'][0]['name'] == 'kikoo2'
    assert all_metas['metas'][0]['value'] == 'lol2'


def test_create_dup_meta(user, job_user_id):
    data = {'name': 'kikoo', 'value': 'lol'}
    meta = user.post('/api/v1/jobs/%s/metas' % job_user_id, data=data)
    meta = user.post('/api/v1/jobs/%s/metas' % job_user_id, data=data)
    assert meta.status_code == 409
