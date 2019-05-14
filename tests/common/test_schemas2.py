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
from dci.common.schemas2 import check_json_is_valid, Properties


def test_check_json_is_valid():
    schema = {"type": "object", "properties": {"name": Properties.string}}
    try:
        check_json_is_valid(schema, {"name": "foo"})
    except DCIException:
        pytest.fail("check_json_is_valid raises DCIException and it should not")  # noqa


def test_check_json_is_valid_required_field():
    schema = {
        "type": "object",
        "properties": {"name": Properties.string},
        "required": ["name"],
    }
    with pytest.raises(DCIException) as e:
        check_json_is_valid(schema, {})
    result = e.value
    assert result.status_code == 400
    assert len(result.payload["errors"]) == 1
    assert result.payload["errors"][0] == "'name' is a required property"
    assert result.message == "Request malformed"


def test_check_json_is_valid_no_additional_properties():
    schema = {
        "type": "object",
        "properties": {"name": Properties.string},
        "additionalProperties": False,
    }
    with pytest.raises(DCIException) as e:
        check_json_is_valid(schema, {"name": "foo", "age": 32})
    result = e.value
    assert result.status_code == 400
    assert len(result.payload["errors"]) == 1
    assert result.payload["errors"][0] == "Additional properties are not allowed ('age' was unexpected)"  # noqa
    assert result.message == "Request malformed"


def test_check_json_is_valid_check_string_type():
    schema = {
        "type": "object",
        "properties": {"name": Properties.string},
        "required": ["name"],
    }
    try:
        check_json_is_valid(schema, {"name": "good string"})
    except DCIException:
        pytest.fail("Properties.string is invalid")

    with pytest.raises(DCIException) as e:
        check_json_is_valid(schema, {"name": None})
    errors = e.value.payload["errors"]
    assert len(errors) == 1
    assert errors[0] == "name: None is not of type 'string'"


def test_check_json_is_valid_check_uuid_type():
    schema = {
        "type": "object",
        "properties": {"uuid": Properties.uuid},
        "required": ["uuid"],
    }
    try:
        check_json_is_valid(schema, {"uuid": "506e5ef5-5db8-410e-b566-a85d1ca24946"})  # noqa
    except DCIException:
        pytest.fail("Properties.uuid is invalid")

    with pytest.raises(DCIException) as e:
        check_json_is_valid(schema, {"uuid": "not an uuid"})
    errors = e.value.payload["errors"]
    assert len(errors) == 1
    assert errors[0] == "uuid: 'not an uuid' is not a valid 'uuid'"


def test_check_json_is_valid_check_email_type():
    schema = {
        "type": "object",
        "properties": {"email": Properties.email},
        "required": ["email"],
    }
    try:
        check_json_is_valid(schema, {"email": "contact+dci@example.org"})
    except DCIException:
        pytest.fail("Properties.email is invalid")

    with pytest.raises(DCIException) as e:
        check_json_is_valid(schema, {"email": "not an email"})
    errors = e.value.payload["errors"]
    assert len(errors) == 1
    assert errors[0] == "'not an email' is not a 'email'"


def test_check_json_is_valid_check_url_type():
    schema = {
        "type": "object",
        "properties": {"url": Properties.url},
        "required": ["url"],
    }
    try:
        check_json_is_valid(schema, {"url": "https://distributed-ci.io"})
    except DCIException:
        pytest.fail("Properties.url is invalid")

    with pytest.raises(DCIException) as e:
        check_json_is_valid(schema, {"url": "not an url"})
    errors = e.value.payload["errors"]
    assert len(errors) == 1
    assert errors[0] == "url: 'not an url' is not a valid 'url'"


def test_check_json_is_valid_check_json_type():
    schema = {
        "type": "object",
        "properties": {"json": Properties.json},
        "required": ["json"],
    }
    try:
        check_json_is_valid(schema, {"json": {"a": 1}})
        check_json_is_valid(schema, {"json": {"nested": {"a": 1}}})
    except DCIException:
        pytest.fail("Properties.json is invalid")

    with pytest.raises(DCIException) as e:
        check_json_is_valid(schema, {"json": "not an json"})
    errors = e.value.payload["errors"]
    assert len(errors) == 1
    assert errors[0] == "'not an json' is not of type 'object'"


def test_check_json_is_valid_check_array_type():
    schema = {
        "type": "object",
        "properties": {"array": Properties.array},
        "required": ["array"],
    }
    try:
        check_json_is_valid(schema, {"array": []})
        check_json_is_valid(schema, {"array": ["1", "2"]})
    except DCIException:
        pytest.fail("Properties.array is invalid")

    with pytest.raises(DCIException) as e:
        check_json_is_valid(schema, {"array": "not an array"})
    errors = e.value.payload["errors"]
    assert len(errors) == 1
    assert errors[0] == "array: 'not an array' is not of type 'array'"


def test_check_json_is_valid_check_integer_type():
    schema = {
        "type": "object",
        "properties": {"integer": Properties.integer},
        "required": ["integer"],
    }
    try:
        check_json_is_valid(schema, {"integer": 1})
        check_json_is_valid(schema, {"integer": -1})
    except DCIException:
        pytest.fail("Properties.integer is invalid")

    with pytest.raises(DCIException) as e:
        check_json_is_valid(schema, {"integer": "not an integer"})
    errors = e.value.payload["errors"]
    assert len(errors) == 1
    assert errors[0] == "integer: 'not an integer' is not of type 'integer'"


def test_check_json_is_valid_check_positive_integer_type():
    schema = {
        "type": "object",
        "properties": {"positive_integer": Properties.positive_integer},
        "required": ["positive_integer"],
    }
    try:
        check_json_is_valid(schema, {"positive_integer": 1})
    except DCIException:
        pytest.fail("Properties.positive_integer is invalid")

    with pytest.raises(DCIException) as e:
        check_json_is_valid(schema, {"positive_integer": -1})
    errors = e.value.payload["errors"]
    assert len(errors) == 1
    assert errors[0] == "positive_integer: -1 is less than the minimum of 1"

    with pytest.raises(DCIException) as e:
        check_json_is_valid(schema, {"positive_integer": 0})
    errors = e.value.payload["errors"]
    assert len(errors) == 1
    assert errors[0] == "positive_integer: 0 is less than the minimum of 1"


def test_check_json_is_valid_check_positive_or_null_integer_type():
    schema = {
        "type": "object",
        "properties": {"positive_or_null_integer": Properties.positive_or_null_integer},  # noqa
        "required": ["positive_or_null_integer"],
    }
    try:
        check_json_is_valid(schema, {"positive_or_null_integer": 0})
    except DCIException:
        pytest.fail("Properties.positive_or_null_integer is invalid")


def test_check_json_is_valid_check_string_integer_type():
    schema = {
        "type": "object",
        "properties": {"string_integer": Properties.string_integer},
        "required": ["string_integer"],
    }
    try:
        check_json_is_valid(schema, {"string_integer": "1"})
        check_json_is_valid(schema, {"string_integer": "-1"})
    except DCIException as e:
        pytest.fail("Properties.string_integer is invalid")

    with pytest.raises(DCIException) as e:
        check_json_is_valid(schema, {"string_integer": "not an string_integer"})  # noqa
    errors = e.value.payload["errors"]
    assert len(errors) == 1
    assert errors[0] == "string_integer: 'not an string_integer' is not an integer"  # noqa


def test_check_json_is_valid_check_positive_string_integer_type():
    schema = {
        "type": "object",
        "properties": {"positive_string_integer": Properties.positive_string_integer},  # noqa
        "required": ["positive_string_integer"],
    }
    try:
        check_json_is_valid(schema, {"positive_string_integer": "1"})
    except DCIException as e:
        pytest.fail("Properties.positive_string_integer is invalid")

    with pytest.raises(DCIException) as e:
        check_json_is_valid(schema, {"positive_string_integer": "-1"})
    errors = e.value.payload["errors"]
    assert len(errors) == 1
    assert errors[0] == "positive_string_integer: '-1' is not a positive integer"  # noqa

    with pytest.raises(DCIException) as e:
        check_json_is_valid(schema, {"positive_string_integer": "0"})
    errors = e.value.payload["errors"]
    assert len(errors) == 1
    assert errors[0] == "positive_string_integer: '0' is not a positive integer"  # noqa


def test_check_json_is_valid_check_positive_or_null_string_integer_type():
    schema = {
        "type": "object",
        "properties": {"positive_or_null_string_integer": Properties.positive_or_null_string_integer},  # noqa
        "required": ["positive_or_null_string_integer"],
    }
    try:
        check_json_is_valid(schema, {"positive_or_null_string_integer": "0"})
    except DCIException:
        pytest.fail("Properties.positive_or_null_string_integer is invalid")


def test_check_json_is_valid_check_key_value_csv_type():
    schema = {
        "type": "object",
        "properties": {"kvcsv": Properties.key_value_csv},
        "required": ["kvcsv"],
    }
    try:
        check_json_is_valid(schema, {"kvcsv": "k1:v1"})
        check_json_is_valid(schema, {"kvcsv": "k1:v1,k2:v2"})
    except DCIException:
        pytest.fail("Properties.kvcsv is invalid")

    with pytest.raises(DCIException) as e:
        check_json_is_valid(schema, {"kvcsv": "k1 v1"})
    errors = e.value.payload["errors"]
    assert len(errors) == 1
    assert errors[0] == "kvcsv: 'k1 v1' is not a 'key value csv'"
