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

from uuid import UUID
from io import BytesIO

import mock
import six
from sqlalchemy import sql

from dci.api.v1 import transformations
from dci.db import models
from dci.stores.swift import Swift
from dci.common import utils
from tests.data import JUNIT

SWIFT = 'dci.stores.swift.Swift'

JSONUNIT = {
    'success': 3,
    'failures': 1,
    'errors': 1,
    'skips': 1,
    'regressions': 0,
    'successfixes': 0,
    'total': 6,
    'time': 9759,
    'testscases': [
        {
            'name': 'test_1',
            'classname': 'classname_1',
            'time': 0.02311568802,
            'action': 'skipped',
            'regression': False,
            'successfix': False,
            'message': 'skip message',
            'type': 'skipped',
            'value': 'test skipped'
        },
        {
            'name': 'test_2',
            'classname': 'classname_1',
            'time': 0.91562318802,
            'action': 'error',
            'regression': False,
            'successfix': False,
            'message': 'error message',
            'type': 'error',
            'value': 'test in error'
        },
        {
            'name': 'test_3',
            'classname': 'classname_1',
            'time': 0.18802915623,
            'action': 'failure',
            'regression': False,
            'successfix': False,
            'message': 'failure message',
            'type': 'failure',
            'value': 'test in failure'
        },
        {
            'name': 'test_4',
            'classname': 'classname_1',
            'time': 2.91562318802,
            'action': 'passed',
            'regression': False,
            'successfix': False,
            'message': '',
            'type': '',
            'value': ''
        },
        {
            'name': 'test_5',
            'classname': 'classname_1',
            'time': 3.23423443444,
            'action': 'passed',
            'regression': False,
            'successfix': False,
            'message': '',
            'type': '',
            'value': 'STDOUT'
        },
        {
            'name': 'test_6',
            'classname': 'classname_1',
            'time': 2.48294832443,
            'action': 'passed',
            'regression': False,
            'successfix': False,
            'message': '',
            'type': '',
            'value': 'STDERR'
        },
    ]
}


def test_junit2dict():
    result = transformations.junit2dict(BytesIO(JUNIT.encode('utf-8')))

    assert result == JSONUNIT


def test_junit2dict_with_ansible_run_vyos_integration_tests_xml():
    with open('tests/data/ansible-run-vyos-integration-tests.xml', 'rb') as f:
        result = transformations.junit2dict(f)

    assert result['success'] == 293
    assert result['errors'] == 0
    assert result['failures'] == 0
    assert result['skips'] == 10
    assert result['total'] == 303
    assert result['time'] == 368722
    assert len(result['testscases']) == 303


def test_junit2dict_with_ansible_run_ovs_integration_tests_xml():
    with open('tests/data/ansible-run-ovs-integration-tests.xml', 'r') as f:
        result = transformations.junit2dict(f)

    assert result['success'] == 16
    assert result['errors'] == 0
    assert result['failures'] == 0
    assert result['skips'] == 1
    assert result['total'] == 17
    assert result['time'] == 42321
    assert len(result['testscases']) == 17


def test_junit2dict_with_tempest_xml():
    with open('tests/data/tempest-results.xml', 'r') as f:
        result = transformations.junit2dict(f)

    assert result['success'] == 117
    assert result['errors'] == 0
    assert result['failures'] == 1
    assert result['skips'] == 13
    assert result['total'] == 131
    assert result['time'] == 1318612
    assert len(result['testscases']) == 131
    assert result['testscases'][126]['value'] == "Ironic is not enabled."
    assert 'Traceback (most recent call last):' in result['testscases'][130]['value']


def test_junit2dict_with_rally_xml():
    with open('tests/data/rally-results.xml', 'r') as f:
        result = transformations.junit2dict(f)

    assert result['success'] == 16
    assert result['errors'] == 0
    assert result['failures'] == 0
    assert result['skips'] == 0
    assert result['total'] == 16
    assert result['time'] == 1186390
    assert len(result['testscases']) == 16


def test_junit2dict_with_cki_xml():
    with open('tests/data/cki-results.xml', 'r') as f:
        result = transformations.junit2dict(f)
    print(result)
    assert result['success'] == 2
    assert result['errors'] == 1
    assert result['failures'] == 0
    assert result['skips'] == 0
    assert result['total'] == 3
    assert result['time'] == 0
    assert len(result['testscases']) == 3


def test_junit2dict_invalid():
    # remove the first closing testcase tag, in order to make the json invalid
    invalid_junit = JUNIT.replace('</testcase>', '', 1)
    result = transformations.junit2dict(BytesIO(invalid_junit.encode('utf-8')))

    assert 'ParseError' in result['error']


def test_retrieve_junit2dict(admin, job_user_id):
    with mock.patch(SWIFT, spec=Swift) as mock_swift:
        mockito = mock.MagicMock()

        head_result = {
            'etag': utils.gen_etag(),
            'content-type': 'stream',
            'content-length': 7
        }
        mockito.head.return_value = head_result

        def get(a):
            return True, six.StringIO(JUNIT),

        mockito.get = get
        mock_swift.return_value = mockito
        headers = {
            'DCI-NAME': 'junit_file.xml',
            'DCI-JOB-ID': job_user_id,
            'DCI-MIME': 'application/junit',
            'Content-Disposition': 'attachment; filename=junit_file.xml',
            'Content-Type': 'application/junit'
        }

        file = admin.post('/api/v1/files', headers=headers, data=JUNIT)
        file_id = file.data['file']['id']

        # First retrieve file
        res = admin.get('/api/v1/files/%s/content' % file_id)

        assert res.data == JUNIT

        # Non Regression Test: XHR doesn't modify content
        headers = {'X-Requested-With': 'XMLHttpRequest'}
        res = admin.get('/api/v1/files/%s/content' % file_id, headers=headers)

        assert res.data == JUNIT
        assert res.headers['Content-Type'] == 'application/junit'


def test_create_file_fill_tests_results_table(engine, admin, job_user_id):
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
        mockito.get.return_value = [True, six.StringIO(content_file)]
        mock_swift.return_value = mockito

        headers = {
            'DCI-JOB-ID': job_user_id,
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
    assert test_result['name'] == 'tempest-results.xml'
    assert test_result['total'] == 131
    assert test_result['skips'] == 13
    assert test_result['failures'] == 1
    assert test_result['errors'] == 0
    assert test_result['success'] == 117
    assert test_result['time'] == 1318612


def test_add_regressions_successfix():
    old_junit = """
<testsuite errors="0" failures="60" name="" tests="2289" time="3385.127">
    <testcase classname="Testsuite1" name="test_1" time="28.810">
        <failure type="Exception">Traceback</failure>
    </testcase>
    <testcase classname="Testsuite1" name="test_2" time="29.419" />
    <testcase classname="Testsuite1" name="test_3" time="29.419" />
</testsuite>
"""
    new_junit = """
<testsuite errors="0" failures="60" name="" tests="2289" time="3385.127">
    <testcase classname="Testsuite1" name="test_1" time="28.810" />
    <testcase classname="Testsuite1" name="test_2" time="29.419">
        <failure type="Exception">Traceback</failure>
    </testcase>
    <testcase classname="Testsuite1" name="test_3" time="29.419">
        <failure type="Exception">Traceback</failure>
    </testcase>
</testsuite>
"""
    old_tests = transformations.junit2dict(BytesIO(old_junit.encode('utf-8')))
    new_tests = transformations.junit2dict(BytesIO(new_junit.encode('utf-8')))
    tests = transformations.add_regressions_and_successfix_to_tests(
        old_tests,
        new_tests
    )
    assert tests['successfixes'] == 1
    assert tests['regressions'] == 2


def test_junit2dict_with_big_xml():
    with open('tests/data/run_nxos_integration_tests.xml', 'r') as f:
        result = transformations.junit2dict(f)

    assert result['success'] == 10306
    assert result['errors'] == 2
    assert result['failures'] == 4
    assert result['skips'] == 1170
    assert result['total'] == 11482
    assert result['time'] == 17010679
    assert len(result['testscases']) == 11482
