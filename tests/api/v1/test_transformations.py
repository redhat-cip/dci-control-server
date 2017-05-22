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
from tests.data import JUNIT

SWIFT = 'dci.stores.swift.Swift'

JSONUNIT = {
    'success': 1,
    'failures': 1,
    'errors': 1,
    'skips': 1,
    'total': 4,
    'time': 4042,
    'testscases': [
        {
            'name': 'test_1',
            'classname': 'classname_1',
            'time': 0.02311568802,
            'action': 'skipped',
            'message': 'skip message',
            'type': 'skipped',
            'value': 'test skipped'
        },
        {
            'name': 'test_2',
            'classname': 'classname_1',
            'time': 0.91562318802,
            'action': 'error',
            'message': 'error message',
            'type': 'error',
            'value': 'test in error'
        },
        {
            'name': 'test_3',
            'classname': 'classname_1',
            'time': 0.18802915623,
            'action': 'failure',
            'message': 'failure message',
            'type': 'failure',
            'value': 'test in failure'
        },
        {
            'name': 'test_4',
            'classname': 'classname_1',
            'time': 2.91562318802,
            'action': 'passed',
            'message': '',
            'type': '',
            'value': ''
        },
    ]
}


def test_junit2dict():
    result = transformations.junit2dict(JUNIT)

    assert result == JSONUNIT


def test_junit2dict_with_tempest_xml():
    with open('tests/data/tempest-results.xml', 'r') as f:
        content_file = f.read()
        result = transformations.junit2dict(content_file)

    assert result['success'] == 117
    assert result['errors'] == 0
    assert result['failures'] == 0
    assert result['skips'] == 13
    assert result['total'] == 130
    assert result['time'] == 1308365
    assert len(result['testscases']) == 130


def test_junit2dict_with_rally_xml():
    with open('tests/data/rally-results.xml', 'r') as f:
        content_file = f.read()
        result = transformations.junit2dict(content_file)

    assert result['success'] == 16
    assert result['errors'] == 0
    assert result['failures'] == 0
    assert result['skips'] == 0
    assert result['total'] == 16
    assert result['time'] == 1186390
    assert len(result['testscases']) == 16


def test_junit2dict_invalid():
    # remove the first closing testcase tag, in order to make the json invalid
    invalid_junit = JUNIT.replace('</testcase>', '', 1)
    result = transformations.junit2dict(invalid_junit)

    assert 'XMLSyntaxError' in result['error']


def test_junit2dict_empty():
    result = transformations.junit2dict('')

    assert result == {}


def test_retrieve_junit2dict(admin, job_id):
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
                'attachment; filename="junit_file.xml"')
        expect_data = JSONUNIT.copy()
        expect_data['name'] = 'junit_file.xml'
        assert json.loads(res.data) == expect_data


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
    assert test_result['name'] == 'tempest-results.xml'
    assert test_result['total'] == 130
    assert test_result['skips'] == 13
    assert test_result['failures'] == 0
    assert test_result['errors'] == 0
    assert test_result['success'] == 117
    assert test_result['time'] == 1308365
