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
import json

import dci
import logging
import lxml.etree as ET
import os
import pkg_resources

LOG = logging.getLogger(__name__)


def junit2json(string):
    if not string:
        return '{}'

    xslt = ET.fromstring(pkg_resources.resource_string(
        dci.__name__, os.path.join('data', 'junittojson.xsl')
    ))
    try:
        dom = ET.fromstring(string)
        for tc in dom.xpath('//testcase'):
            if len(tc.xpath('child::*')) > 0:
                to_clean_string = tc.xpath('child::*')[0].text or ''

                # 1. Replace " by '
                to_clean_string = to_clean_string.replace('"', "'")
                # 2. Replace \n by \\n
                to_clean_string = to_clean_string.replace('\n', '\\n')

                tc.xpath('child::*')[0].text = to_clean_string

        transform = ET.XSLT(xslt)
        string = str(transform(dom))
    except ET.XMLSyntaxError as e:
        string = '{ "error": "XMLSyntaxError: %s " }' % str(e)
        LOG.info('transformations.junittojson: XMLSyntaxError %s' % str(e))

    return string


def format_test_result(test_result):
    r = {
        'name': u'',
        'total': 0,
        'skips': 0,
        'failures': 0,
        'errors': 0,
        'success': 0,
        'time': 0.0
    }
    try:
        r['name'] = test_result['name']
        for field in ['total', 'skips', 'failures', 'errors']:
            if field in test_result and test_result[field]:
                r[field] = int(test_result[field])
        r['success'] = (r['total'] - r['failures'] - r['errors'] - r['skips'])
        if 'time' in test_result and test_result['time']:
            r['time'] = int(float(test_result['time']) * 1000)
    except Exception as e:
        LOG.exception(e)
        LOG.debug(test_result)
    return r


def junit2dict(content_file):
    malformed_dict = json.loads(junit2json(content_file))
    return format_test_result(malformed_dict)
