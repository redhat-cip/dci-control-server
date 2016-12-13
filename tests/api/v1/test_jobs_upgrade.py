# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Red Hat, Inc
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


def test_job_upgrade(admin, job_id, remoteci_id, topic_id, topic_user_id):
    job_upgraded = admin.post('/api/v1/jobs/upgrade',
                              data={'remoteci_id': remoteci_id,
                                    'topic_id': topic_user_id,
                                    'job_id': job_id})

    topic = admin.get('/api/v1/topics/%s' % topic_user_id)
    topic_etag = topic.data['topic']['etag']

    # the topic does not contains a 'next_topic' field
    assert job_upgraded.status_code == 400

    # adds a next topic
    assert admin.put('/api/v1/topics/%s' % topic_user_id,
                     data={'next_topic': topic_id},
                     headers={'If-match': topic_etag}).status_code == 204

    # request for the upgrade of the first job
    job_upgraded = admin.post('/api/v1/jobs/upgrade',
                              data={'remoteci_id': remoteci_id,
                                    'topic_id': topic_user_id,
                                    'job_id': job_id})
    job_upgraded_id = job_upgraded.data['job']['id']
    assert job_upgraded.status_code == 201
    assert job_upgraded.data['job']['upgrade_job'] is True
    # job_upgraded is a job against the next version of jobdefinition

    original_job = admin.get('/api/v1/jobs/%s' % job_id)

    # check that the first job is link to the new one
    assert original_job.data['job']['upgraded_job_id'] == job_upgraded_id
