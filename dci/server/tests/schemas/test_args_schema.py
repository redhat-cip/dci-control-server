# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Red Hat, Inc
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

import dci.server.common.exceptions as exceptions
import dci.server.common.schemas as schemas
import dci.server.utils as utils

import pytest

data = {
    'limit': '50',
    'offset': '10',
    'sort': 'field_1,field_2',
    'where': 'field_1:value_1,field_2:value_2',
    'embed': 'resource_1,resource_2'
}

data_expected = {
    'limit': 50,
    'offset': 10,
    'sort': ['field_1', 'field_2'],
    'where': ['field_1:value_1', 'field_2:value_2'],
    'embed': ['resource_1', 'resource_2']
}


def _invalid_args(data, errors):
    with pytest.raises(exceptions.DCIException) as exc:
        schemas.args(data)

    assert exc.value.payload == {'errors': errors}


def test_extra_args():
    extra_data = utils.dict_merge(data, {'foo': 'bar'})
    assert schemas.args(extra_data) == data_expected


def test_default_args():
    expected = {'limit': 20, 'offset': 0, 'sort': [], 'where': [], 'embed': []}
    assert schemas.args({}) == expected


def test_invalid_args():
    errors = {'limit': schemas.INVALID_LIMIT,
              'offset': schemas.INVALID_OFFSET}

    data = {'limit': -1, 'offset': -1}
    _invalid_args(data, errors)
    data = {'limit': 'foo', 'offset': 'bar'}
    _invalid_args(data, errors)


def test_args():
    assert schemas.args(data) == data_expected
