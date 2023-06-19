# -*- encoding: utf-8 -*-
#
# Copyright (C) 2023 Red Hat, Inc.
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

from dci.db import query_dsl

import pyparsing as pp
import pytest


def test_query_invalid():
    with pytest.raises(pp.ParseException):
        query_dsl.parse("toto")


def test_query_valid():
    ret = query_dsl.parse("eq(name,openshift-vanilla)")
    assert ret == [["eq", "name", "openshift-vanilla"]]


def test_query_complex_1():
    ret = query_dsl.parse(
        "and(eq(name,openshift-vanilla),not_contains(tags,ocp-vanilla-4.12-ok)))"
    )
    assert ret == [
        "and",
        ["eq", "name", "openshift-vanilla"],
        ["not_contains", "tags", "ocp-vanilla-4.12-ok"],
    ]


def test_query_complex_2():
    ret = query_dsl.parse(
        "and(eq(name,openshift-vanilla),not_contains(tags,build:ga),not(null(url)))"
    )
    assert ret == [
        "and",
        ["eq", "name", "openshift-vanilla"],
        ["not_contains", "tags", "build:ga"],
        ["not", ["null", "url"]],
    ]


def test_nrt_query_ordering():
    ret = query_dsl.parse(
        "and(eq(state,active),contains(tags,nightly),or(eq(type,compose),eq(type,compose-noinstall)))"
    )
    assert ret == [
        "and",
        ["eq", "state", "active"],
        ["contains", "tags", "nightly"],
        ["or", ["eq", "type", "compose"], ["eq", "type", "compose-noinstall"]],
    ]
    ret = query_dsl.parse(
        "and(or(eq(type,compose),eq(type,compose-noinstall)),eq(state,active),contains(tags,nightly))"
    )
    assert ret == [
        "and",
        ["or", ["eq", "type", "compose"], ["eq", "type", "compose-noinstall"]],
        ["eq", "state", "active"],
        ["contains", "tags", "nightly"],
    ]
