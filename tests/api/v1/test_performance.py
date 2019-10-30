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

from __future__ import unicode_literals

from tests import data as tests_data
import tests.utils as t_utils

import collections

FileDesc = collections.namedtuple('FileDesc', ['name', 'content'])
SWIFT = 'dci.stores.swift.Swift'


def test_compare_performance(user, remoteci_context, team_user_id, topic, topic_user_id):  # noqa
    # create the baseline job
    j_baseline = remoteci_context.post(
        '/api/v1/jobs/schedule',
        data={'topic_id': topic['id']}
    )
    j_baseline = j_baseline.data['job']
    data = {'job_id': j_baseline['id'], 'status': 'success'}
    js_baseline = remoteci_context.post(
        '/api/v1/jobstates',
        data=data).data['jobstate']
    f_1 = t_utils.post_file(user, js_baseline['id'],
                            FileDesc('PBO_Results',
                                     tests_data.jobtest_one),
                            mime='application/junit')
    assert f_1 is not None

    # create the second job
    job2 = remoteci_context.post(
        '/api/v1/jobs/schedule',
        data={'topic_id': topic['id']}
    )
    job2 = job2.data['job']
    data = {'job_id': job2['id'], 'status': 'success'}
    js_job2 = remoteci_context.post(
        '/api/v1/jobstates',
        data=data).data['jobstate']
    f_1 = t_utils.post_file(user, js_job2['id'],
                            FileDesc('PBO_Results',
                                     tests_data.jobtest_two),
                            mime='application/junit')
    assert f_1 is not None

    res = user.get('/api/v1/performance',
                   headers={'Content-Type': 'application/json'},
                   data={'base_job_id': j_baseline['id'],
                         'jobs': [job2['id']],
                         'test_filename': 'PBO_Results'})
    assert res.status_code == 200
