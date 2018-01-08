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

import logging
from lxml import etree
from datetime import timedelta

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


def junit2dict(string):
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
        return failures_2 - failures_1
    except etree.XMLSyntaxError as e:
        LOG.error('XMLSyntaxError %s' % str(e))
