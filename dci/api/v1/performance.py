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

import flask

from dci.api.v1 import api
from dci.api.v1 import utils as v1_utils
from dci.api.v1 import export_control
from dci.api.v1 import files
from dci.api.v1 import transformations
from dci.common.schemas import (
    check_json_is_valid,
    performance_schema
)
from dci.db import models
from dci import decorators

import logging
from sqlalchemy import sql

LOG = logging.getLogger(__name__)


def _add_delta_to_tests(base_tests, testscases):
    res = []
    for t in testscases:
        res_test = {}
        res_test['classname'] = t.get('classname')
        res_test['name'] = t.get('name')
        key = "%s/%s" % (t.get('classname'), t.get('name'))
        if t.get("time") is None or base_tests.get(key) is None:
            continue

        base_time = float(base_tests.get(key))
        t_time = float(t.get('time'))
        diff = t_time - base_time
        percentage = (diff * 100.) / base_time
        res_test['time'] = t_time
        res_test['delta'] = percentage
        res.append(res_test)
    return res


def _keytify_test_cases(test_cases):
    """Traverse the test cases list and return a dictionnary
    which associate test case name to its duration. This is used for
    fast access to tests cases duration.
    """
    res = {}
    for tc in test_cases:
        key = "%s/%s" % (tc.get('classname'), tc.get('name'))
        if tc.get('time') is None or float(tc.get('time')) == 0.0:
            continue
        res[key] = float(tc.get('time'))
    return res


def get_performance_tests(baseline_tests, tests):

    res = []
    # baseline_tests is processed first because file descriptor
    # is fully read (junit2dict) once
    base_dict = transformations.junit2dict(baseline_tests['fd'])
    base_dict_testscases = base_dict['testscases']
    base_dict = _keytify_test_cases(base_dict['testscases'])
    test = _add_delta_to_tests(base_dict, base_dict_testscases)
    res.append({'job_id': baseline_tests['job_id'],
                'topic': baseline_tests['topic'],
                'testscases': test})

    for t in tests:
        test = transformations.junit2dict(t['fd'])
        test = _add_delta_to_tests(base_dict, test['testscases'])
        res.append({'job_id': t['job_id'],
                    'topic': t['topic'],
                    'testscases': test})
    return res


def _get_topic_of_job(job_id):
    query = sql.select([models.TOPICS]). \
        select_from(
            models.JOBS.join(
                models.TOPICS,
                models.JOBS.c.topic_id == models.TOPICS.c.id)). \
        where(models.JOBS.c.id == job_id)
    return flask.g.db_conn.execute(query).fetchone()


def _get_test_files(base_job_id, jobs_ids, test_filename):
    """"for each job get the associated file corresponding to the
    provided filename"""

    def _get_file(job_id):
        query = sql.select([models.FILES]). \
            where(models.FILES.c.job_id == job_id). \
            where(models.FILES.c.name == test_filename)
        return flask.g.db_conn.execute(query).fetchone()

    res = []
    for j_id in [base_job_id] + jobs_ids:
        j = v1_utils.verify_existence_and_get(j_id, models.JOBS, _raise=False)
        if j is None:
            LOG.error("job %s not found" % j_id)
            continue
        file = _get_file(j_id)
        if file is None:
            LOG.error("file %s from job %s not found" % (test_filename, j_id))  # noqa
            continue
        topic = _get_topic_of_job(j_id)
        if topic is None:
            LOG.error("topic of job %s not found" % j_id)
            continue
        res.append({'file': file, 'job_id': j_id, 'topic': topic['name']})
    if len(res) > 1:
        return res[0], res[1:]
    return None, None


def _get_tests_filenames(base_job_id):
    query = sql.select([models.FILES.c.name]). \
        where(models.FILES.c.job_id == base_job_id). \
        where(models.FILES.c.mime == 'application/junit')
    res = flask.g.db_conn.execute(query).fetchall()
    if res is None:
        return []
    else:
        return [r[0] for r in res]


def _get_test_files_with_fds(baseline_tests_file, tests_files):
    res = []
    for tf in [baseline_tests_file] + tests_files:
        fd = files.get_file_descriptor(tf['file'])
        res.append({"fd": fd, "job_id": tf["job_id"], "topic": tf["topic"]})
    if len(res) > 1:
        return res[0], res[1:]
    else:
        return res[0], None


@api.route('/performance', methods=['POST'])
@decorators.login_required
def compare_performance(user):
    values = flask.request.json
    check_json_is_valid(performance_schema, values)
    base_job_id = values["base_job_id"]
    jobs_ids = values["jobs"]
    for job_id in [base_job_id] + jobs_ids:
        v1_utils.verify_existence_and_get(job_id, models.JOBS)
        topic = _get_topic_of_job(job_id)
        export_control.verify_access_to_topic(user, topic)

    tests_filenames = _get_tests_filenames(base_job_id)
    res = []
    for tf in tests_filenames:
        baseline_tests, tests = _get_test_files(base_job_id, jobs_ids, tf)  # noqa
        baseline_tests_file_with_fd, tests_files_with_fds = _get_test_files_with_fds(baseline_tests, tests)  # noqa
        perf_res = get_performance_tests(baseline_tests_file_with_fd,
                                         tests_files_with_fds)
        res.append({tf: perf_res})
    return flask.jsonify({"performance": res}), 200
