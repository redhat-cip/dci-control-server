# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 Red Hat, Inc
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

from io import BytesIO
from dci.api.v1 import junit


def test_get_testsuites_from_junit():
    junit_file = BytesIO(
        """<?xml version='1.0' encoding='utf-8'?>
<testsuites errors="1" failures="1" tests="6" time="24">
    <testsuite errors="1" failures="0" name="testsuite 1" skipped="1" tests="3" time="4">
        <properties>
            <property name="testcase_2_property_1" value="tc2p1" />
        </properties>
        <testcase classname="classname_1" name="testcase_1" time="1">
            <skipped message="skip message" type="skipped">test skipped</skipped>
        </testcase>
        <testcase classname="classname_1" name="testcase_2" time="1">
            <error message="error message" type="error">test in error</error>
        </testcase>
        <testcase classname="classname_2" name="testcase_3" time="2">
            <system-out>stdout preserve
line returned</system-out>
            <system-err></system-err>
        </testcase>
    </testsuite>
    <testsuite errors="0" failures="1" name="testsuite 2" skipped="0" tests="3" time="20">
        <testcase classname="classname_1" name="testcase_1" time="5">
            <failure message="failure message" type="failure">test in failure</failure>
        </testcase>
        <testcase classname="classname_1" name="testcase_2" time="5"/>
        <testcase classname="classname_2" name="testcase_3" time="10"/>
    </testsuite>
</testsuites>""".encode(
            "utf-8"
        )
    )
    assert junit.get_testsuites_from_junit(junit_file) == [
        {
            "id": 0,
            "name": "testsuite 1",
            "tests": 3,
            "failures": 0,
            "errors": 1,
            "skipped": 1,
            "success": 1,
            "time": 4.0,
            "properties": [
                {
                    "name": "testcase_2_property_1",
                    "value": "tc2p1",
                },
            ],
            "testcases": [
                {
                    "name": "testcase_1",
                    "classname": "classname_1",
                    "time": 1.0,
                    "action": "skipped",
                    "message": "skip message",
                    "type": "skipped",
                    "value": "test skipped",
                    "stdout": None,
                    "stderr": None,
                    "properties": [],
                },
                {
                    "name": "testcase_2",
                    "classname": "classname_1",
                    "time": 1.0,
                    "action": "error",
                    "message": "error message",
                    "type": "error",
                    "value": "test in error",
                    "stdout": None,
                    "stderr": None,
                    "properties": [],
                },
                {
                    "name": "testcase_3",
                    "classname": "classname_2",
                    "time": 2.0,
                    "action": "success",
                    "message": None,
                    "type": None,
                    "value": "",
                    "stdout": "stdout preserve\nline returned",
                    "stderr": None,
                    "properties": [],
                },
            ],
        },
        {
            "id": 1,
            "name": "testsuite 2",
            "tests": 3,
            "failures": 1,
            "errors": 0,
            "skipped": 0,
            "success": 2,
            "time": 20.0,
            "properties": [],
            "testcases": [
                {
                    "name": "testcase_1",
                    "classname": "classname_1",
                    "time": 5.0,
                    "action": "failure",
                    "message": "failure message",
                    "type": "failure",
                    "value": "test in failure",
                    "stdout": None,
                    "stderr": None,
                    "properties": [],
                },
                {
                    "name": "testcase_2",
                    "classname": "classname_1",
                    "time": 5.0,
                    "action": "success",
                    "message": None,
                    "type": None,
                    "value": "",
                    "stdout": None,
                    "stderr": None,
                    "properties": [],
                },
                {
                    "name": "testcase_3",
                    "classname": "classname_2",
                    "time": 10.0,
                    "action": "success",
                    "message": None,
                    "type": None,
                    "value": "",
                    "stdout": None,
                    "stderr": None,
                    "properties": [],
                },
            ],
        },
    ]


def test_update_testcases_with_state_changes():
    previous_junit_file = BytesIO(
        """<?xml version='1.0' encoding='utf-8'?>
<testsuite errors="0" failures="1" name="testsuite_1" tests="4" time="40">
    <testcase classname="classname_1" name="testcase_1" time="10">
        <failure type="Exception">Traceback</failure>
    </testcase>
    <testcase classname="classname_1" name="testcase_2" time="10" />
    <testcase classname="classname_1" name="testcase_3" time="10" />
    <testcase classname="classname_1" name="testcase_4" time="10" />
</testsuite>""".encode(
            "utf-8"
        )
    )
    junit_file = BytesIO(
        """<?xml version='1.0' encoding='utf-8'?>
<testsuite errors="0" failures="1" name="testsuite_1" tests="4" time="40">
    <testcase classname="classname_1" name="testcase_1" time="10" />
    <testcase classname="classname_1" name="testcase_2" time="10">
        <failure type="Exception">Traceback</failure>
    </testcase>
    <testcase classname="classname_1" name="testcase_3" time="10" />
    <testcase classname="classname_1" name="testcase_5" time="10" />
</testsuite>""".encode(
            "utf-8"
        )
    )

    previous_testsuites = junit.get_testsuites_from_junit(previous_junit_file)
    testsuites = junit.get_testsuites_from_junit(junit_file)
    testsuites = junit.update_testsuites_with_testcase_changes(
        previous_testsuites, testsuites
    )
    assert testsuites[0]["testcases"] == [
        {
            "name": "testcase_1",
            "classname": "classname_1",
            "time": 10.0,
            "action": "success",
            "message": None,
            "type": None,
            "value": "",
            "stdout": None,
            "stderr": None,
            "properties": [],
            "successfix": True,
            "regression": False,
            "state": "RECOVERED",
        },
        {
            "name": "testcase_2",
            "classname": "classname_1",
            "time": 10.0,
            "action": "failure",
            "message": None,
            "type": "Exception",
            "value": "Traceback",
            "stdout": None,
            "stderr": None,
            "properties": [],
            "successfix": False,
            "regression": True,
            "state": "REGRESSED",
        },
        {
            "name": "testcase_3",
            "classname": "classname_1",
            "time": 10.0,
            "action": "success",
            "message": None,
            "type": None,
            "value": "",
            "stdout": None,
            "stderr": None,
            "properties": [],
            "successfix": False,
            "regression": False,
            "state": "UNCHANGED",
        },
        {
            "name": "testcase_4",
            "classname": "classname_1",
            "time": 10.0,
            "action": "success",
            "message": None,
            "type": None,
            "value": "",
            "stdout": None,
            "stderr": None,
            "properties": [],
            "successfix": False,
            "regression": False,
            "state": "REMOVED",
        },
        {
            "name": "testcase_5",
            "classname": "classname_1",
            "time": 10.0,
            "action": "success",
            "message": None,
            "type": None,
            "value": "",
            "stdout": None,
            "stderr": None,
            "properties": [],
            "successfix": False,
            "regression": False,
            "state": "ADDED",
        },
    ]
    assert testsuites[0]["successfixes"] == 1
    assert testsuites[0]["regressions"] == 1
    assert testsuites[0]["additions"] == 1
    assert testsuites[0]["deletions"] == 1
    assert testsuites[0]["unchanged"] == 1


def test_update_testcases_with_state_changes_with_no_previous_junit():
    junit_file = BytesIO(
        """<?xml version='1.0' encoding='utf-8'?>
<testsuite errors="0" failures="2" name="testsuite_1" tests="3" time="33">
    <testcase classname="classname_1" name="testcase_1" time="11" />
    <testcase classname="classname_1" name="testcase_2" time="12">
        <failure type="Exception">Traceback</failure>
    </testcase>
    <testcase classname="classname_1" name="testcase_3" time="10">
        <failure type="Exception">Traceback</failure>
    </testcase>
</testsuite>""".encode(
            "utf-8"
        )
    )

    previous_testsuites = None
    testsuites = junit.get_testsuites_from_junit(junit_file)
    testsuites = junit.update_testsuites_with_testcase_changes(
        previous_testsuites, testsuites
    )

    assert testsuites[0]["testcases"] == [
        {
            "name": "testcase_1",
            "classname": "classname_1",
            "time": 11.0,
            "action": "success",
            "message": None,
            "type": None,
            "value": "",
            "stdout": None,
            "stderr": None,
            "properties": [],
            "successfix": False,
            "regression": False,
            "state": "ADDED",
        },
        {
            "name": "testcase_2",
            "classname": "classname_1",
            "time": 12.0,
            "action": "failure",
            "message": None,
            "type": "Exception",
            "value": "Traceback",
            "stdout": None,
            "stderr": None,
            "properties": [],
            "successfix": False,
            "regression": False,
            "state": "ADDED",
        },
        {
            "name": "testcase_3",
            "classname": "classname_1",
            "time": 10.0,
            "action": "failure",
            "message": None,
            "type": "Exception",
            "value": "Traceback",
            "stdout": None,
            "stderr": None,
            "properties": [],
            "successfix": False,
            "regression": False,
            "state": "ADDED",
        },
    ]
    assert testsuites[0]["successfixes"] == 0
    assert testsuites[0]["regressions"] == 0
    assert testsuites[0]["additions"] == 3
    assert testsuites[0]["deletions"] == 0
    assert testsuites[0]["unchanged"] == 0


def test_nrt_get_testsuites_from_junit_with_an_empty_junit():
    junit_file = BytesIO()
    assert junit.get_testsuites_from_junit(junit_file) == []
