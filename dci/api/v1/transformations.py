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


def parse_testsuite(root):
    return {
        'name': root.attrib.get('name'),
        'classname': root.attrib.get('classname'),
        'time': float(root.attrib.get('time'))
    }


def parse_testcase(root):
    classes = {
        'failure': 'failures',
        'error': 'errors',
        'skipped': 'skips',
    }
    tag_element = root.tag
    if tag_element in classes.keys():
        return {
            'message': root.attrib.get('message', ''),
            'value': root.text,
            'action': tag_element,
            'type': classes[tag_element]
        }


def junit2dict(string):
    if not string:
        return {}
    results = {
        'success': 0,
        'errors': 0,
        'failures': 0,
        'skips': 0,
        'total': 0,
        'testscases': []
    }
    try:
        test_duration = timedelta(seconds=0)
        root = etree.fromstring(string)
        for subroot in root:
            results['total'] = results['total'] + 1
            testscase = parse_testsuite(subroot)
            test_duration += timedelta(seconds=testscase['time'])
            for el in subroot:
                test_result = parse_testcase(el)
                if test_result:
                    results[test_result['type']] += 1
                    testscase['result'] = test_result
            results['testscases'].append(testscase)
        results['success'] = (results['total'] -
                              results['failures'] -
                              results['errors'] -
                              results['skips'])
        results['time'] = int(test_duration.total_seconds() * 1000)
    except etree.XMLSyntaxError as e:
        results['error'] = "XMLSyntaxError: %s " % str(e)
        LOG.error('XMLSyntaxError %s' % str(e))
    return results
