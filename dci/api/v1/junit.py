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

from xml.etree import ElementTree
from xml.parsers.expat import errors as xml_errors
from datetime import timedelta


def parse_time(string_value):
    try:
        return float(string_value)
    except:
        return 0.0


def parse_properties(root):
    properties = []
    for child in root:
        tag = child.tag
        if tag != "property":
            continue
        property_name = child.get("name", "").strip()
        property_value = child.get("value", "")
        if property_name:
            properties.append({"name": property_name, "value": property_value})
    return properties


def parse_testcase(testcase_xml):
    testcase = {
        "name": testcase_xml.attrib.get("name", ""),
        "classname": testcase_xml.attrib.get("classname", ""),
        "time": parse_time(testcase_xml.attrib.get("time", "0")),
        "action": "success",
        "message": None,
        "type": None,
        "value": "",
        "stdout": None,
        "stderr": None,
        "properties": [],
    }
    for testcase_child in testcase_xml:
        tag = testcase_child.tag
        if tag not in [
            "skipped",
            "error",
            "failure",
            "system-out",
            "system-err",
        ]:
            continue
        text = testcase_child.text
        if tag == "system-out":
            testcase["stdout"] = text
        elif tag == "system-err":
            testcase["stderr"] = text
        else:
            testcase["action"] = tag
            testcase["message"] = testcase_child.get("message", None)
            testcase["type"] = testcase_child.get("type", None)
            testcase["value"] = text
        testcase_child.clear()
    return testcase


def parse_testsuite(testsuite_xml):
    testsuite = {
        "id": 0,
        "name": testsuite_xml.attrib.get("name", ""),
        "tests": 0,
        "failures": 0,
        "errors": 0,
        "skipped": 0,
        "success": 0,
        "time": 0,
        "testcases": [],
        "properties": [],
    }
    testsuite_duration = timedelta(seconds=0)
    for testcase_xml in testsuite_xml:
        tag = testcase_xml.tag
        if tag == "testcase":
            testcase = parse_testcase(testcase_xml)
            testsuite_duration += timedelta(seconds=testcase["time"])
            testsuite["tests"] += 1
            action = testcase["action"]
            if action == "skipped":
                testsuite["skipped"] += 1
            elif action == "error":
                testsuite["errors"] += 1
            elif action == "failure":
                testsuite["failures"] += 1
            else:
                testsuite["success"] += 1
            testsuite["testcases"].append(testcase)
        elif tag == "properties":
            testsuite["properties"] = parse_properties(testcase_xml)
    testsuite["time"] = testsuite_duration.total_seconds()
    return testsuite


def get_testsuites_from_junit(file_descriptor):
    try:
        testsuites = []
        nb_of_testsuites = 0
        for event, element in ElementTree.iterparse(file_descriptor):
            if element.tag == "testsuite":
                testsuite = parse_testsuite(element)
                testsuite["id"] = nb_of_testsuites
                nb_of_testsuites += 1
                testsuites.append(testsuite)
                element.clear()
        return testsuites
    except ElementTree.ParseError as parse_error:
        error_code_no_elements = xml_errors.codes[xml_errors.XML_ERROR_NO_ELEMENTS]
        if parse_error.code == error_code_no_elements:
            return []
        raise parse_error


def _get_unique_testcase_key(testsuite, testcase):
    return "%s:%s:%s" % (testsuite["name"], testcase["classname"], testcase["name"])


def _compare_testsuites(testsuite1, testsuite2):
    testcases1_map = {}
    if testsuite1:
        for testcase in testsuite1["testcases"]:
            testcase_key = _get_unique_testcase_key(testsuite1, testcase)
            testcases1_map[testcase_key] = testcase

    testcases2_map = {}
    for testcase in testsuite2["testcases"]:
        testcase_key = _get_unique_testcase_key(testsuite2, testcase)
        testcases2_map[testcase_key] = testcase

    testcases1_keys = set(testcases1_map.keys())
    testcases2_keys = set(testcases2_map.keys())

    testcases = []
    removed_testcases = testcases1_keys - testcases2_keys
    for removed_testcase_key in removed_testcases:
        testcase = testcases1_map[removed_testcase_key]
        testcase["successfix"] = False  # tobedeleted
        testcase["regression"] = False  # tobedeleted
        testcase["state"] = "REMOVED"
        testcases.append(testcase)

    added_testcases = testcases2_keys - testcases1_keys
    for added_testcase_key in added_testcases:
        testcase = testcases2_map[added_testcase_key]
        testcase["successfix"] = False  # tobedeleted
        testcase["regression"] = False  # tobedeleted
        testcase["state"] = "ADDED"
        testcases.append(testcase)

    successfixes = 0
    regressions = 0
    unchanged = 0
    for testcase_key_in_both in testcases1_keys & testcases2_keys:
        previous_testcase = testcases1_map[testcase_key_in_both]
        testcase = testcases2_map[testcase_key_in_both]
        testcase["successfix"] = False
        testcase["regression"] = False
        if previous_testcase["action"] == testcase["action"]:
            testcase["state"] = "UNCHANGED"
            unchanged += 1
        else:
            if previous_testcase["action"] == "success":
                testcase["state"] = "REGRESSED"
                testcase["regression"] = True  # tobedeleted
                regressions += 1
            else:
                testcase["state"] = "RECOVERED"
                testcase["successfix"] = True  # tobedeleted
                successfixes += 1
        testcases.append(testcase)

    testsuite2["testcases"] = sorted(testcases, key=lambda d: d["name"])
    testsuite2["successfixes"] = successfixes
    testsuite2["regressions"] = regressions
    testsuite2["additions"] = len(added_testcases)
    testsuite2["deletions"] = len(removed_testcases)
    testsuite2["unchanged"] = unchanged
    return testsuite2


def update_testsuites_with_testcase_changes(testsuites1, testsuites2):
    testsuites1_map = {ts["name"]: ts for ts in testsuites1 or []}
    testsuites = []
    for testsuite in testsuites2:
        previous_testsuite = testsuites1_map.get(testsuite["name"])
        testsuites.append(_compare_testsuites(previous_testsuite, testsuite))
    return testsuites


def calculate_test_results(testsuites):
    results = {
        "success": 0,
        "failures": 0,
        "errors": 0,
        "skipped": 0,
        "tests": 0,
        "regressions": 0,
        "successfixes": 0,
        "time": 0,
    }
    for testsuite in testsuites:
        results["success"] += testsuite["success"]
        results["failures"] += testsuite["failures"]
        results["errors"] += testsuite["errors"]
        results["skipped"] += testsuite["skipped"]
        results["tests"] += testsuite["tests"]
        results["regressions"] += testsuite["regressions"]
        results["successfixes"] += testsuite["successfixes"]
        results["time"] += testsuite["time"]
    return results
