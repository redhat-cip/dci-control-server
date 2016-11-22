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


def test_create_meta(user, job_user_id):
    meta = user.post('/api/v1/jobs/%s/metas' % job_user_id,
                     data={'name': 'kikoo', 'value': 'lol'})
    assert meta.status_code == 201


def test_delete_meta(user, job_user_id):
    meta = user.post('/api/v1/jobs/%s/metas' % job_user_id,
                     data={'name': 'kikoo', 'value': 'lol'})
    meta_id = meta.data['id']
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
