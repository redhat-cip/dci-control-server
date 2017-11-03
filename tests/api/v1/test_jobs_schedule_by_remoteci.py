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

import uuid


def test_schedule_jobs(remoteci, team_id, remoteci_id,
                       topic_id, components_ids):
    headers = {
        'User-Agent': 'thisismyuseragent',
        'Client-Version': 'python-dciclient_0.1.0'
    }
    job = remoteci.post('/api/v1/jobs/schedule', headers=headers,
                     data={'remoteci_id': remoteci_id,
                           'topic_id': topic_id})

    print(job)
    assert job.status_code == 201
    job = job.data['job']
    assert job['topic_id'] == topic_id
    assert job['team_id'] == team_id
    assert job['remoteci_id'] == remoteci_id
    assert job['user_agent'] == headers['User-Agent']
    assert job['client_version'] == headers['Client-Version']
    assert job['allow_upgrade_job'] is True
    assert job['rconfiguration_id'] is None
