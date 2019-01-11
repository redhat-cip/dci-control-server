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
        'regression': False,
        'successfix': False,
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
        'regressions': 0,
        'successfixes': 0,
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


def add_regressions_and_successfix_to_tests(testsuite1, testsuite2):
    # dict from testcase's name to each testcase itself for fast access
    testscases1_map = dict()
    for testcase in testsuite1['testscases']:
        testcase['name'] = testcase['name'].split('[')[0]
        testname = '%s:%s' % (testcase['classname'], testcase['name'])
        testscases1_map[testname] = testcase

    for testcase in testsuite2['testscases']:
        testcase['name'] = testcase['name'].split('[')[0]
        testname = '%s:%s' % (testcase['classname'], testcase['name'])
        # this is a new test then ignore it
        if testname not in testscases1_map:
            continue
        prev_testcase = testscases1_map[testname]
        # if switch from success to failure then its a regression
        if testcase['action'] == 'failure':
            if (prev_testcase['action'] == 'passed' or
                    prev_testcase['regression']):
                testcase['regression'] = True
                testsuite2['regressions'] += 1
        # if switch from either failure/regression to success its successfix
        elif testcase['action'] == 'passed':
            if (prev_testcase['action'] == 'failure' or
                    prev_testcase['regression']):
                testcase['successfix'] = True
                testsuite2['successfixes'] += 1
    return testsuite2


def add_known_issues_to_tests(testsuite, tests_to_issues):
    for testcase in testsuite['testscases']:
        if testcase['action'] == 'failure':
            testcase['name'] = testcase['name'].split('[')[0]
            testname = '%s:%s' % (testcase['classname'], testcase['name'])
            if testname in tests_to_issues:
                testcase['issues'] = tests_to_issues[testname]
            else:
                testcase['issues'] = []
    return testsuite
