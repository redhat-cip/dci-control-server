# -*- coding: utf-8 -*-
#
# Copyright (C) Red Hat, Inc
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


def test_create_tag(admin, user, job_user_id):
    admin.post('/api/v1/tags', data={'name': 'kikoo'})
    tag = user.post('/api/v1/jobs/%s/tags' % job_user_id,
                    data={'name': 'kikoo'})
    assert tag.status_code == 201
    job = user.get('/api/v1/jobs/%s' % job_user_id).data
    assert job['job']['tag'] == ['kikoo']


def test_implicit_creation_of_tag(admin, user, job_user_id):
    tag = user.post('/api/v1/jobs/%s/tags' % job_user_id,
                    data={'name': 'kikooo'})
    assert tag.status_code == 201


def test_get_all_tags(admin, user, job_user_id):
    admin.post('/api/v1/tags', data={'name': 'kikoo'})
    admin.post('/api/v1/tags', data={'name': 'kikoo2'})

    user.post('/api/v1/jobs/%s/tags' % job_user_id,
              data={'name': 'kikoo'})
    user.post('/api/v1/jobs/%s/tags' % job_user_id,
              data={'name': 'kikoo2'})

    all_tags = user.get('/api/v1/jobs/%s/tags' % job_user_id).data
    assert len(all_tags['tags']) == 2
    all_tags = {t['name'] for t in all_tags['tags']}
    assert all_tags == {'kikoo', 'kikoo2'}

    all_tags_embeds = user.get('/api/v1/jobs/%s?embed=tags' % job_user_id).data   # noqa
    assert len(all_tags_embeds['job']['tags']) == 2
    all_tags_embeds = {t['name'] for t in all_tags_embeds['job']['tags']}
    assert all_tags_embeds == {'kikoo', 'kikoo2'}

    job = user.get('/api/v1/jobs/%s' % job_user_id).data
    assert set(job['job']['tag']) == {'kikoo', 'kikoo2'}


def test_delete_tag(admin, user, job_user_id):
    tag = admin.post('/api/v1/tags', data={'name': 'kikoo'})
    tag_id = tag.data['tag']['id']

    user.post('/api/v1/jobs/%s/tags' % job_user_id,
              data={'name': 'kikoo'})

    job = user.get('/api/v1/jobs/%s' % job_user_id).data
    assert set(job['job']['tag']) == {'kikoo'}

    all_tags = user.get('/api/v1/jobs/%s/tags' % job_user_id).data
    assert len(all_tags['tags']) == 1

    tag_deleted = user.delete('/api/v1/jobs/%s/tags/%s' % (job_user_id,
                                                           tag_id))
    assert tag_deleted.status_code == 204

    all_tags = user.get('/api/v1/jobs/%s/tags' % job_user_id).data
    assert len(all_tags['tags']) == 0
    job = user.get('/api/v1/jobs/%s' % job_user_id).data
    assert job['job']['tag'] == []


def test_filter_job_by_tag(user, remoteci_context, components_user_ids,
                           topic_user_id):

    data = {
        'comment': 'kikoolol',
        'components': components_user_ids,
        'topic_id': topic_user_id
    }
    # create job 1
    job = remoteci_context.post('/api/v1/jobs', data=data)
    job_id_1 = job.data['job']['id']
    remoteci_context.post('/api/v1/jobs/%s/tags' % job_id_1,
                          data={'name': 'tag_1'})
    remoteci_context.post('/api/v1/jobs/%s/tags' % job_id_1,
                          data={'name': 'debug'})

    # create job 2
    job = remoteci_context.post('/api/v1/jobs', data=data)
    job_id_2 = job.data['job']['id']
    remoteci_context.post('/api/v1/jobs/%s/tags' % job_id_2,
                          data={'name': 'tag_2'})
    remoteci_context.post('/api/v1/jobs/%s/tags' % job_id_2,
                          data={'name': 'debug'})

    res = user.get('/api/v1/jobs?where=tag:tag_1')
    assert len(res.data['jobs']) == 1
    assert 'tag_1' in res.data['jobs'][0]['tag']

    res = user.get('/api/v1/jobs?where=tag:debug')
    assert len(res.data['jobs']) == 2
    assert 'debug' in res.data['jobs'][0]['tag']
    assert 'debug' in res.data['jobs'][1]['tag']
