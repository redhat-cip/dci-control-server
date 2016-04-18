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

import dci
import logging
import lxml.etree as ET
import os
import pkg_resources

LOG = logging.getLogger('__name__')


def junittojson(result):

    xslt = ET.fromstring(
        pkg_resources.resource_string(dci.__name__,
                                      os.path.join('data', 'junittojson.xsl'))
    )
    if not result['content']:
        result['content'] = '{}'
    else:
        try:
            dom = ET.fromstring(result['content'])
            for tc in dom.xpath('//testcase'):
                if len(tc.xpath('child::*')) > 0:
                    to_clean_string = tc.xpath('child::*')[0].text or ''

                    # 1. Replace " by '
                    to_clean_string = to_clean_string.replace('"', "'")
                    # 2. Replace \n by \\n
                    to_clean_string = to_clean_string.replace('\n', '\\n')

                    tc.xpath('child::*')[0].text = to_clean_string

            transform = ET.XSLT(xslt)
            result['content'] = str(transform(dom))
        except ET.XMLSyntaxError as e:
            result['content'] = '{ "error": "XMLSyntaxError: %s " }' % str(e)
            LOG.info('transformations.junittojson: XMLSyntaxError %s' % str(e))

    return result


def transform(results):

    for result in results:
        if result['mime'] == 'application/junit':
            result = junittojson(result)

    return results
