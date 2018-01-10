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

from dci.db import models

import flask
import logging
from lxml import etree
from datetime import timedelta

from sqlalchemy import sql

LOG = logging.getLogger(__name__)


def parse_testcase(root):
    return {
        'name': root.attrib.get('name', ''),
        'classname': root.attrib.get('classname', ''),
        'time': float(root.attrib.get('time', 0))
    }


def parse_action(root):
    return {
        'message': root.get('message', ''),
        'value': root.text,
        'action': root.tag if root.tag not in ['system-out', 'system-err']
        else 'passed',
        'type': root.get('type', '')
    }


def parse_testscases(root):
    testscases = []
    for testcase in root.findall('testcase'):
        testcase_dict = {
            'action': 'passed',
            'message': '',
            'type': '',
            'value': ''
        }
        testcase_dict.update(parse_testcase(testcase))
        if len(testcase) > 0:
            action = parse_action(testcase[0])
            testcase_dict.update(action)
        testscases.append(testcase_dict)
    return testscases


def parse_testssuites(root):
    testssuites = []
    for testsuite in root.findall('testsuite'):
        testssuites.append(testsuite)
    if not testssuites:
        testssuites.append(root)
    return testssuites


def parse_regressions(regressions):
    test_case_dict = {'name': '',
                      'classname': '',
                      'time': '',
                      'message': '',
                      'value': '',
                      'action': 'regression',
                      'type': ''}
    results = []
    for regression in regressions:
        classname, name = regression.split(':')
        test_case = dict(test_case_dict)
        test_case['classname'] = classname
        test_case['name'] = name
        results.append(test_case)

    return results


def junit2dict(string, regressions=None):
    if not string:
        return {}
    results = {
        'success': 0,
        'errors': 0,
        'failures': 0,
        'skips': 0,
        'total': 0,
        'testscases': [],
        'time': 0,
    }
    try:
        root = etree.fromstring(string)
        testssuites = parse_testssuites(root)

        for testsuite in testssuites:
            testscases = parse_testscases(testsuite)

            test_duration = timedelta(seconds=0)
            for testcase in testscases:
                results['total'] += 1
                test_duration += timedelta(seconds=float(testcase['time']))
                if testcase['action'] == 'skipped':
                    results['skips'] += 1
                if testcase['action'] == 'error':
                    results['errors'] += 1
                if testcase['action'] == 'failure':
                    results['failures'] += 1
                results['testscases'].append(testcase)

            results['success'] = (results['total'] -
                                  results['failures'] -
                                  results['errors'] -
                                  results['skips'])
            if regressions is not None:
                regressions = parse_regressions(regressions)
                results['testscases'].extend(regressions)
            results['time'] += int(test_duration.total_seconds() * 1000)
    except etree.XMLSyntaxError as e:
        results['error'] = "XMLSyntaxError: %s " % str(e)
        LOG.error('XMLSyntaxError %s' % str(e))
    return results


def get_regressions_failures(testsuite1, testsuite2):
    """Given two junit testsuite, this function will compute the failures
    that happen in testsuite2 and not in testsuite1."""

    def get_testcases_on_failure(string_testsuite):
        root = etree.fromstring(string_testsuite).getroottree()
        result = set()
        # xpath to get only the testcase tags which includes the tag 'failure'
        testcases_on_failure = root.xpath('./testcase/failure/..')
        for testcase in testcases_on_failure:
            classname = testcase.attrib.get('classname')
            name = testcase.attrib.get('name')
            result.add('%s:%s' % (classname, name))
        # result is a set containing all the tests names
        return result

    try:
        failures_1 = get_testcases_on_failure(testsuite1)
        failures_2 = get_testcases_on_failure(testsuite2)
        # returns the difference of the two sets
        return list(failures_2 - failures_1)
    except etree.XMLSyntaxError as e:
        LOG.error('XMLSyntaxError %s' % str(e))


def get_regressions(swift, job, filename, team_id, current_test_suite):
    """Get previous job of the passed job and compute regression agains the
    file referenced by 'filename'."""
    def _get_previous_job_in_topic(job):
        topic_id = job['topic_id']
        query = sql.select([models.JOBS]). \
            where(sql.and_(models.JOBS.c.topic_id == topic_id,
                           models.JOBS.c.created_at < job['created_at'],
                           models.JOBS.c.id != job['id'],
                           models.JOBS.c.state != 'archived')). \
            order_by(sql.desc(models.JOBS.c.created_at))
        return flask.g.db_conn.execute(query).fetchone()

    def _get_file_from_job(job_id, filename):
        query = sql.select([models.FILES]). \
            where(sql.and_(models.FILES.c.name == filename,
                           models.FILES.c.job_id == job_id))
        return flask.g.db_conn.execute(query).fetchone()

    prev_job = _get_previous_job_in_topic(job)
    if prev_job is not None:
        prev_job_file = _get_file_from_job(prev_job['id'], filename)
        if prev_job_file is not None:
            prev_file_path = swift.build_file_path(
                team_id,
                prev_job['id'],
                prev_job_file['id'])
            _, prev_file_descriptor = swift.get(prev_file_path)
            prev_test_suite = prev_file_descriptor.read()
            return get_regressions_failures(prev_test_suite,
                                            current_test_suite)
    return []
