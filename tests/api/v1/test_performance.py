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

from dci.api.v1 import performance
from dci.api.v1 import transformations

from tests import data as tests_data
import tests.utils as t_utils

import collections

FileDesc = collections.namedtuple('FileDesc', ['name', 'content'])


def test_compare_performance(user, remoteci_context, team_user_id, topic):

    def _create_job(pbo_result, tempest_result):

        # create the baseline job
        _job = remoteci_context.post(
            '/api/v1/jobs/schedule',
            data={'topic_id': topic['id']}
        )
        _job = _job.data['job']
        data = {'job_id': _job['id'], 'status': 'success'}
        js_baseline = remoteci_context.post(
            '/api/v1/jobstates',
            data=data).data['jobstate']
        f_1 = t_utils.post_file(user, js_baseline['id'],
                                FileDesc('PBO_Results',
                                         pbo_result),
                                mime='application/junit')
        assert f_1 is not None

        f_11 = t_utils.post_file(user, js_baseline['id'],
                                 FileDesc('Tempest',
                                          tempest_result),
                                 mime='application/junit')
        assert f_11 is not None
        return _job

    job_baseline_1 = _create_job(tests_data.jobtest_one,
                                 tests_data.jobtest_one)

    job_baseline_2 = _create_job(tests_data.jobtest_one_bis,
                                 tests_data.jobtest_one_bis)

    job_3 = _create_job(tests_data.jobtest_two,
                        tests_data.jobtest_two)

    res = user.post('/api/v1/performance',
                    headers={'Content-Type': 'application/json'},
                    data={'base_jobs_ids': [job_baseline_1['id'],
                                            job_baseline_2['id']],
                          'jobs': [job_3['id']]})

    expected = {'Testsuite_1/test_1': 20.,
                'Testsuite_1/test_2': -25.,
                'Testsuite_1/test_3[id-2fc6822e-b5a8-42ed-967b-11d86e881ce3,smoke]': 25.}  # noqa

    perf = res.data['performance']
    for tests in perf:
        filename = list(tests.keys())[0]
        for t in tests[filename]:
            assert t['topic'] == 'OSP12'
            for tc in t['testscases']:
                k = '%s/%s' % (tc['classname'], tc['name'])
                assert expected[k] == tc['delta']


def test_get_performance_tests():
    baseline_test = open('tests/data/perf_test_baseline.xml', 'r')
    baseline_test = transformations.junit2dict(baseline_test)
    baseline_test['topic'] = 'topic1'
    test = open('tests/data/perf_test.xml', 'r')

    perf_res = performance.get_performance_tests(baseline_test,
                                                 [{'fd': test,
                                                   'job_id': 'test',
                                                   'topic': 'topic2'}])

    expected = {'ci': 930.0, 'rs2': 900.0, 'exit_code': -90.0}
    for tc in perf_res[0]['testscases']:
        assert expected[tc['name']] == tc['delta']


def test_compare_performance_permission(user2, remoteci_context, team_user_id, topic):  # noqa
    # create the baseline job
    job_baseline = remoteci_context.post(
        '/api/v1/jobs/schedule',
        data={'topic_id': topic['id']}
    )
    job_baseline = job_baseline.data['job']

    # create the second job
    job2 = remoteci_context.post(
        '/api/v1/jobs/schedule',
        data={'topic_id': topic['id']}
    )
    job2 = job2.data['job']

    res = user2.post('/api/v1/performance',
                     headers={'Content-Type': 'application/json'},
                     data={'base_jobs_ids': [job_baseline['id']],
                           'jobs': [job2['id']]})
    assert res.status_code == 401


def test_compare_performance_job_not_found(user, remoteci_context, topic):
    res = user.post('/api/v1/performance',
                    headers={'Content-Type': 'application/json'},
                    data={'base_jobs_ids': ['69c5067b-f3ef-417a-a254-e7027dbe2ea8'],  # noqa
                          'jobs': ['69c5067b-f3ef-417a-a254-e7027dbe2ea8']})
    assert res.status_code == 404

    job_baseline = remoteci_context.post(
        '/api/v1/jobs/schedule',
        data={'topic_id': topic['id']}
    )
    job_baseline_id = job_baseline.data['job']['id']

    res = user.post('/api/v1/performance',
                    headers={'Content-Type': 'application/json'},
                    data={'base_jobs_ids': [job_baseline_id],
                          'jobs': ['69c5067b-f3ef-417a-a254-e7027dbe2ea8']})
    assert res.status_code == 404
