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

import json
from uuid import UUID

import mock
from sqlalchemy import sql

from dci.api.v1 import transformations
from dci.db import models
from dci.stores.swift import Swift
from dci.common import utils

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
            'content-type': 'stream',
            'content-length': 7
        }

        mockito.head.return_value = head_result
        mockito.get.return_value = ['', JUNIT]
        mockito.get_object.return_value = JUNIT
        mock_swift.return_value = mockito
        headers = {
            'DCI-NAME': 'junit_file.xml', 'DCI-JOB-ID': job_id,
            'DCI-MIME': 'application/junit',
            'Content-Disposition': 'attachment; filename=junit_file.xml',
            'Content-Type': 'application/junit'
        }

        file = admin.post('/api/v1/files', headers=headers, data=JUNIT)
        file_id = file.data['file']['id']

        # First retrieve file
        res = admin.get('/api/v1/files/%s/content' % file_id)

        assert res.data == JUNIT

        # Now retrieve it through XHR
        headers = {'X-Requested-With': 'XMLHttpRequest'}
        res = admin.get('/api/v1/files/%s/content' % file_id, headers=headers)

        assert (res.headers.get('Content-Disposition') ==
                'attachment; filename=junit_file.xml')
        assert json.loads(res.data) == JSONUNIT


def test_create_file_fill_tests_results_table(engine, admin, job_id):
    with open('tests/data/tempest-results.xml', 'r') as f:
        content_file = f.read()
    with mock.patch(SWIFT, spec=Swift) as mock_swift:
        mockito = mock.MagicMock()
        head_result = {
            'etag': utils.gen_etag(),
            'content-type': 'stream',
            'content-length': 7
        }
        mockito.head.return_value = head_result
        mockito.get_object.return_value = content_file
        mock_swift.return_value = mockito

        headers = {
            'DCI-JOB-ID': job_id,
            'DCI-NAME': 'tempest-results.xml',
            'DCI-MIME': 'application/junit',
            'Content-Disposition': 'attachment; filename=tempest-results.xml',
            'Content-Type': 'application/junit'
        }
        admin.post('/api/v1/files', headers=headers, data=content_file)

    query = sql.select([models.TESTS_RESULTS])
    tests_results = engine.execute(query).fetchall()
    test_result = dict(tests_results[0])

    assert len(tests_results) == 1
    assert UUID(str(test_result['id']), version=4)
    assert test_result['name'] == ''
    assert test_result['total'] == 130
    assert test_result['skips'] == 0
    assert test_result['failures'] == 0
    assert test_result['errors'] == 0
    assert test_result['success'] == 130
    assert test_result['time'] == 996679


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


def test_junit2dict_with_tempest_xml():
    with open('tests/data/tempest-results.xml', 'r') as f:
        content_file = f.read()
        result = transformations.junit2dict(content_file)

    assert result['name'] == ''
    assert result['total'] == 130
    assert result['skips'] == 0
    assert result['failures'] == 0
    assert result['errors'] == 0
    assert result['success'] == 130
    assert result['time'] == 996679


def test_junit2dict_with_rally_xml():
    with open('tests/data/rally-results.xml', 'r') as f:
        content_file = f.read()
        result = transformations.junit2dict(content_file)

    assert result['name'] == 'Rally test suite'
    assert result['total'] == 16
    assert result['skips'] == 0
    assert result['failures'] == 0
    assert result['errors'] == 0
    assert result['success'] == 16
    assert result['time'] == 1186410


def test_junit2dict_with_no_tests():
    no_tests = """<testsuite errors="0" failures="0" name="" tests="0"
time="0.307"></testsuite>"""
    result = transformations.junit2dict(no_tests)

    assert result['name'] == ''
    assert result['total'] == 0
    assert result['skips'] == 0
    assert result['failures'] == 0
    assert result['errors'] == 0
    assert result['success'] == 0
    assert result['time'] == 307


def test_junit2dict_partial():
    partial_junit = """<testsuite errors="0" failures="0" name="pytest" skips="1"
                       tests="3" time="46.050"></testsuite>"""
    result = transformations.junit2dict(partial_junit)

    assert result['name'] == 'pytest'
    assert result['total'] == 3
    assert result['skips'] == 1
    assert result['failures'] == 0
    assert result['errors'] == 0
    assert result['success'] == 2
    assert result['time'] == 46050


def test_format_test_result_parse_numbers():
    test_result = transformations.format_test_result({
        'name': u'',
        'total': u'130',
        'skips': 0,
        'failures': u'3',
        'errors': u'5',
        'time': u'1186.41'
    })

    assert type(test_result['total']) == int
    assert type(test_result['skips']) == int
    assert type(test_result['failures']) == int
    assert type(test_result['errors']) == int
    assert type(test_result['time']) == int


def test_format_test_result_calc_success():
    test_result = transformations.format_test_result({
        'name': u'',
        'total': u'150',
        'skips': u'1',
        'failures': u'2',
        'errors': u'3',
    })

    assert test_result['success'] == 150 - 1 - 2 - 3


def test_format_test_result_filter_fields():
    test_result = transformations.format_test_result({
        'invalid_key': u'',
        'name': u'Rally test suite',
        'total': u'16',
        'skips': u'0',
        'failures': u'0',
        'errors': u'0',
        'time': u'1186.12'
    })
    expected_keys = ['name', 'total', 'success', 'skips', 'failures', 'errors',
                     'time']
    assert sorted(test_result.keys()) == sorted(expected_keys)


def test_format_test_result_no_results():
    test_result = transformations.format_test_result({
        'name': u'',
        'total': u'',
        'skips': u'',
        'failures': u'',
        'errors': u'',
        'time': u''
    })

    assert test_result['total'] == 0
    assert test_result['skips'] == 0
    assert test_result['failures'] == 0
    assert test_result['errors'] == 0
    assert test_result['success'] == 0
    assert test_result['time'] == 0
