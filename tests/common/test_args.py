# -*- encoding: utf-8 -*-
#
# Copyright 2018 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import pytest

from dci.common.exceptions import DCIException
from dci.common.schemas2 import check_json_is_valid, args_schema
from dci.common.args import parse_args


def test_args():
    try:
        check_json_is_valid(
            args_schema,
            {
                "limit": "100",
                "offset": "0",
                "sort": "field_1,field_2",
                "where": "field_1:value_1,field_2:value_2",
                "embed": "resource_1,resource_2",
            },
        )
        check_json_is_valid(
            args_schema,
            {
                "limit": "100",
                "offset": "100",
                "sort": "field_1",
                "where": "field_1:value_1",
                "embed": "resource_1",
            },
        )
        check_json_is_valid(args_schema, {})
    except DCIException:
        pytest.fail("args_limit is invalid")


def test_args_invalid_offset_inf_to_zero():
    with pytest.raises(DCIException):
        check_json_is_valid(args_schema, {"limit": "100", "offset": "-100"})


def test_args_invalid_limit_inf_to_zero():
    with pytest.raises(DCIException):
        check_json_is_valid(args_schema, {"limit": "-100", "offset": "0"})


def test_args_invalid_limit_equal_to_zero():
    with pytest.raises(DCIException):
        check_json_is_valid(args_schema, {"limit": "0", "offset": "10"})


def test_args_invalid_where_field():
    with pytest.raises(DCIException):
        check_json_is_valid(args_schema, {"where": "f1:v1;f2:v2"})


def test_args_limit_and_offset_dependent_on_each_other():
    with pytest.raises(DCIException):
        check_json_is_valid(args_schema, {"limit": "100"})

    with pytest.raises(DCIException):
        check_json_is_valid(args_schema, {"offset": "0"})


def test_parse_args():
    args = {
        "limit": "50",
        "offset": "10",
        "sort": "field_1,field_2",
        "where": "field_1:value_1,field_2:value_2",
        "embed": "resource_1,resource_2",
    }
    args_expected = {
        "limit": 50,
        "offset": 10,
        "sort": ["field_1", "field_2"],
        "where": ["field_1:value_1", "field_2:value_2"],
        "embed": ["resource_1", "resource_2"],
    }
    assert parse_args(args) == args_expected


def test_parse_args_empty_args():
    args_expected = {
        "limit": None,
        "offset": None,
        "sort": [],
        "where": [],
        "embed": [],
    }
    assert parse_args({}) == args_expected
