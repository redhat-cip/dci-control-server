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


def test_update_jobs(admin, remoteci_context, job_user_id, topic_user_id):
    # test update schedule latest components
    data = {
        'name': 'pname',
        'type': 'type_1',
        'url': 'http://example.com/',
        'topic_id': topic_user_id,
        'state': 'active'}
    c1 = admin.post('/api/v1/components', data=data).data['component']['id']
    data.update({'type': 'type_2', 'name': 'pname1'})
    c2 = admin.post('/api/v1/components', data=data).data['component']['id']
    data.update({'type': 'type_3', 'name': 'pname2'})
    c3 = admin.post('/api/v1/components', data=data).data['component']['id']
    latest_components = {c1, c2, c3}

    r = remoteci_context.post('/api/v1/jobs/%s/update' % job_user_id)
    assert r.status_code == 201
    update_job = r.data['job']

    assert update_job['update_previous_job_id'] == job_user_id
    assert update_job['topic_id'] == topic_user_id

    update_cmpts = admin.get('/api/v1/jobs/%s/components' % update_job['id'])
    update_cmpts = {cmpt['id'] for cmpt in update_cmpts.data['components']}
    assert latest_components == update_cmpts
