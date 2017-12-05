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


def test_create_tag(user, job_user_id):
    tag = user.post('/api/v1/jobs/%s/tags' % job_user_id,
                     data={'name': 'kikoo', 'value': 'lol'})
    assert tag.status_code == 201


def test_create_tag_without_value(user, job_user_id):
    tag = user.post('/api/v1/jobs/%s/tags' % job_user_id,
                     data={'name': 'kikoo'})
    assert tag.status_code == 201
    tag_id = tag.data['tag']['id']
    tag = user.get('/api/v1/jobs/%s/tags/%s' % (job_user_id, tag_id))
    assert tag.data['tag'][0]['value'] == None


def test_delete_tag(user, job_user_id):
    tag = user.post('/api/v1/jobs/%s/tags' % job_user_id,
                     data={'name': 'kikoo', 'value': 'lol'})
    tag_id = tag.data['tag']['id']
    assert tag.status_code == 201

    tag_deleted = user.delete('/api/v1/jobs/%s/tags/%s' % (job_user_id,
                                                             tag_id))
    assert tag_deleted.status_code == 204

    all_tags = user.get('/api/v1/jobs/%s/tags' % job_user_id).data
    assert not all_tags['tags']


def test_get_all_tags_from_job(user, job_user_id):
    tag_1 = user.post('/api/v1/jobs/%s/tags' % job_user_id,
                       data={'name': 'kikoo', 'value': 'lol'})
    assert tag_1.status_code == 201

    tag_2 = user.post('/api/v1/jobs/%s/tags' % job_user_id,
                       data={'name': 'kikoo2', 'value': 'lol2'})
    assert tag_2.status_code == 201

    all_tags = user.get('/api/v1/jobs/%s/tags' % job_user_id).data
    assert len(all_tags['tags']) == 2


def test_put_tag(user, job_user_id):
    tag = user.post('/api/v1/jobs/%s/tags' % job_user_id,
                     data={'name': 'kikoo', 'value': 'lol'})
    tag_id = tag.data['tag']['id']
    assert tag.status_code == 201
    tag_etag = tag.headers.get("ETag")

    tag_put = user.put('/api/v1/jobs/%s/tags/%s' % (job_user_id, tag_id),
                        data={'name': 'kikoo2', 'value': 'lol2'},
                        headers={'If-match': tag_etag})
    assert tag_put.status_code == 204

    all_tags = user.get('/api/v1/jobs/%s/tags' % job_user_id).data
    assert all_tags['tags']
    assert all_tags['tags'][0]['name'] == 'kikoo2'
    assert all_tags['tags'][0]['value'] == 'lol2'


def test_create_dup_tag(user, job_user_id):
    data = {'name': 'kikoo', 'value': 'lol'}
    tag = user.post('/api/v1/jobs/%s/tags' % job_user_id, data=data)
    tag = user.post('/api/v1/jobs/%s/tags' % job_user_id, data=data)
    assert tag.status_code == 409
