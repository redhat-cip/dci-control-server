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


def parse_junit(file_descriptor):
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


def add_regressions_and_successfix_to_tests(testsuites1, testsuites2):
    testcases_map = {}
    if testsuites1:
        for testsuite in testsuites1:
            for testcase in testsuite["testcases"]:
                testcase_key = _get_unique_testcase_key(testsuite, testcase)
                testcases_map[testcase_key] = testcase

    for testsuite in testsuites2:
        testsuite["successfixes"] = 0
        testsuite["regressions"] = 0
        for testcase in testsuite["testcases"]:
            testcase["successfix"] = False
            testcase["regression"] = False
            testcase_key = _get_unique_testcase_key(testsuite, testcase)
            if testcase_key not in testcases_map:
                continue
            prev_testcase = testcases_map[testcase_key]
            # if switch from success to failure then it's a regression
            if testcase["action"] == "failure":
                if prev_testcase["action"] == "success":
                    testcase["regression"] = True
                    testsuite["regressions"] += 1
            # if switch from either failure/regression to success its successfix
            elif testcase["action"] == "success":
                if prev_testcase["action"] == "failure":
                    testcase["successfix"] = True
                    testsuite["successfixes"] += 1

    return testsuites2


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
