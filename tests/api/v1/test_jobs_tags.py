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


def test_add_tag_to_job(admin, user, job_user_id):
    tag = user.post('/api/v1/jobs/%s/tags' % job_user_id,
                    data={'name': 'kikoo'})
    assert tag.status_code == 201
    job = user.get('/api/v1/jobs/%s' % job_user_id).data
    assert job['job']['tags'] == ['kikoo']


def test_get_all_tags(admin, user, job_user_id):

    user.post('/api/v1/jobs/%s/tags' % job_user_id,
              data={'name': 'kikoo'})
    user.post('/api/v1/jobs/%s/tags' % job_user_id,
              data={'name': 'kikoo2'})

    all_tags = user.get('/api/v1/jobs/%s/tags' % job_user_id).data
    print(all_tags)
    assert len(all_tags['tags']) == 2
    assert set(all_tags['tags']) == {'kikoo', 'kikoo2'}

    job = user.get('/api/v1/jobs/%s' % job_user_id).data
    assert set(job['job']['tags']) == {'kikoo', 'kikoo2'}


def test_delete_tag(admin, user, job_user_id):
    user.post('/api/v1/jobs/%s/tags' % job_user_id,
              data={'name': 'kikoo'})

    job = user.get('/api/v1/jobs/%s' % job_user_id).data
    assert set(job['job']['tags']) == {'kikoo'}

    all_tags = user.get('/api/v1/jobs/%s/tags' % job_user_id).data
    assert len(all_tags['tags']) == 1
    
    assert user.delete('/api/v1/jobs/%s/tags' % job_user_id,
                       data={'name': 'kikoo'}).status_code == 204

    all_tags = user.get('/api/v1/jobs/%s/tags' % job_user_id).data
    assert len(all_tags['tags']) == 0
    job = user.get('/api/v1/jobs/%s' % job_user_id).data
    assert job['job']['tags'] == []


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

    res = user.get('/api/v1/jobs?where=tags:debug,tags:tag_1')
    assert len(res.data['jobs']) == 1

    res = user.get('/api/v1/jobs?where=tags:tag_1')
    assert len(res.data['jobs']) == 1
    assert 'tag_1' in res.data['jobs'][0]['tags']
    assert 'tag_2' not in res.data['jobs'][0]['tags']

    res = user.get('/api/v1/jobs?where=tags:debug')
    assert len(res.data['jobs']) == 2
    assert 'debug' in res.data['jobs'][0]['tags']
    assert 'debug' in res.data['jobs'][1]['tags']
