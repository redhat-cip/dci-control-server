# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Red Hat, Inc
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

import dci.api.v1.transformations as transformations
from dci.stores.swift import Swift
import mock
from dci.common import utils

import json

SWIFT = 'dci.stores.swift.Swift'

JUNIT = """
<testsuite errors="0" failures="0" name="junittojson" skips="1"
           tests="3" time="46.050">
  <properties>
    <property name="x" value="y" />
    <property name="a" value="b" />
  </properties>
  <testcase classname="" file="test-requirements.txt"
            name="test-requirements.txt" time="0.0109479427338">
      <skipped message="all tests skipped by +SKIP option"
               type="pytest.skip">Skipped for whatever reasons</skipped>
  </testcase>
  <testcase classname="tests.test_app" file="tests/test_app.py" line="26"
            name="test_cors_preflight" time="2.91562318802"/>
  <testcase classname="tests.test_app" file="tests/test_app.py" line="42"
            name="test_cors_headers" time="0.574683904648"/>
</testsuite>
"""

JSONUNIT = {
    'name': 'junittojson',
    'failures': '0',
    'errors': '0',
    'skips': '1',
    'total': '3',
    'time': '46.050',
    'properties': [
        {'name': 'x', 'value': 'y'},
        {'name': 'a', 'value': 'b'}
    ],
    'testscases': [
        {
            'name': 'test-requirements.txt',
            'classname': '',
            'file': 'test-requirements.txt',
            'time': u'0.0109479427338',
            'result': {
                'message': 'all tests skipped by +SKIP option',
                'value': 'Skipped for whatever reasons',
                'action': 'skipped',
                'type': 'pytest.skip'
            }
        }, {
            'name': 'test_cors_preflight',
            'classname': 'tests.test_app',
            'file': 'tests/test_app.py',
            'time': '2.91562318802',
            'result': {'action': 'passed'}
        }, {
            'name': 'test_cors_headers',
            'classname': 'tests.test_app',
            'file': 'tests/test_app.py',
            'time': u'0.574683904648',
            'result': {'action': 'passed'},
        }
    ]
}

def test_junit2json_valid():
    result = transformations.junit2json(JUNIT)
    result = json.loads(result)

    assert result['name'] == 'junittojson'
    assert result['total'] == '3'
    assert len(result['properties']) == 2


def test_retrieve_junit2json(admin, job_id):
    with mock.patch(SWIFT, spec=Swift) as mock_swift:

        mockito = mock.MagicMock()

        head_result = {
            'etag': utils.gen_etag(),
            'content-type': "stream",
            'content-length': 7
        }

        mockito.head.return_value = head_result
        mockito.get.return_value = ['', JUNIT]
        mock_swift.return_value = mockito
        headers = {'DCI-NAME': 'junit_file.xml', 'DCI-JOB-ID': job_id,
                   'DCI-MIME': 'application/junit',
                   'Content-Disposition': 'attachment; filename=junit_file.xml',
                   'Content-Type': 'application/junit'}

        file = admin.post('/api/v1/files', headers=headers, data=JUNIT)
        file = file.data['file']['id']

        # First retrieve file
        res = admin.get('/api/v1/files/%s/content' % file)

        assert res.data == JUNIT

        # Now retrieve it through XHR
        headers = {'X-Requested-With': 'XMLHttpRequest'}
        res = admin.get('/api/v1/files/%s/content' % file, headers=headers)

        assert (res.headers.get('Content-Disposition') ==
                'attachment; filename=junit_file.xml')
        assert json.loads(res.data) == JSONUNIT


def test_junit2json_invalid():
    # remove the first closing testcase tag, in order to make the json invalid
    invalid_junit = JUNIT.replace('</testcase>', '', 1)
    result = transformations.junit2json(invalid_junit)
    result = json.loads(result)

    assert 'XMLSyntaxError' in result['error']


def test_junit2json_empty():
    result = transformations.junit2json('')
    result = json.loads(result)

    assert result == {}
