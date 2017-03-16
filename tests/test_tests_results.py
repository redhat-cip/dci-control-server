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

from dci.api.v1 import transformations


def test_junit2dict_with_tempest_xml():
    result = transformations.junit2dict('tests/data/tempest-results.xml')

    assert result['name'] == ''
    assert result['total'] == 130
    assert result['skips'] == 0
    assert result['failures'] == 0
    assert result['errors'] == 0
    assert result['success'] == 130
    assert result['time'] == 996.679


def test_junit2dict_with_rally_xml():
    result = transformations.junit2dict('tests/data/rally-results.xml')

    assert result['name'] == 'Rally test suite'
    assert result['total'] == 16
    assert result['skips'] == 0
    assert result['failures'] == 0
    assert result['errors'] == 0
    assert result['success'] == 16
    assert result['time'] == 1186.41


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
    assert type(test_result['time']) == float


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
    assert test_result['time'] == 0.0
