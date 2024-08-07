# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Red Hat, Inc
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

import logging
from xml.etree import ElementTree
from datetime import timedelta


logger = logging.getLogger(__name__)


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


def parse_element(root):
    testcase = {
        "name": root.attrib.get("name", ""),
        "classname": root.attrib.get("classname", ""),
        "regression": False,
        "successfix": False,
        "time": parse_time(root.attrib.get("time", "0")),
        "message": "",
        "value": "",
        "action": "passed",
        "type": "",
        "stdout": None,
        "stderr": None,
        "properties": [],
    }
    for child in root:
        tag = child.tag
        if tag not in [
            "skipped",
            "error",
            "failure",
            "system-out",
            "system-err",
            "properties",
        ]:
            continue
        text = child.text
        if tag == "system-out":
            testcase["stdout"] = text
        elif tag == "system-err":
            testcase["stderr"] = text
        elif tag == "properties":
            testcase["properties"] = parse_properties(child)
        else:
            testcase["action"] = tag
            testcase["message"] = child.get("message", "")
            testcase["type"] = child.get("type", "")
            testcase["value"] = text
    return testcase


def junit2dict(file_descriptor):
    results = {
        "success": 0,
        "errors": 0,
        "failures": 0,
        "regressions": 0,
        "successfixes": 0,
        "skips": 0,
        "total": 0,
        "testscases": [],
        "time": 0,
    }
    try:
        test_duration = timedelta(seconds=0)
        for event, element in ElementTree.iterparse(file_descriptor):
            if element.tag == "testcase":
                testcase = parse_element(element)
                results["total"] += 1
                time = parse_time(testcase.get("time", "0"))
                test_duration += timedelta(seconds=time)
                action = testcase["action"]
                if action == "skipped":
                    results["skips"] += 1
                if action == "error":
                    results["errors"] += 1
                if action == "failure":
                    results["failures"] += 1
                results["testscases"].append(testcase)
                element.clear()
        results["success"] = (
            results["total"]
            - results["failures"]
            - results["errors"]
            - results["skips"]
        )
        results["time"] += int(test_duration.total_seconds() * 1000)
    except ElementTree.ParseError as pe:
        results["error"] = "ParseError: %s " % str(pe)
        logger.error("ParseError %s" % str(pe))
    except Exception as e:
        results["error"] = "Exception: %s " % str(e)
        logger.exception(e)
    return results


def _concat_classname_and_name(testcase):
    return "%s:%s" % (testcase["classname"], testcase["name"])


def add_regressions_and_successfix_to_tests(testsuite1, testsuite2):
    # dict from testcase's name to each testcase itself for fast access
    testscases1_map = dict()
    for testcase in testsuite1["testscases"]:
        testkey = _concat_classname_and_name(testcase)
        testscases1_map[testkey] = testcase

    for testcase in testsuite2["testscases"]:
        testkey2 = _concat_classname_and_name(testcase)
        # this is a new test then ignore it
        if testkey2 not in testscases1_map:
            continue
        prev_testcase = testscases1_map[testkey2]
        # if switch from success to failure then its a regression
        if testcase["action"] == "failure":
            if prev_testcase["action"] == "passed" or prev_testcase["regression"]:
                testcase["regression"] = True
                testsuite2["regressions"] += 1
        # if switch from either failure/regression to success its successfix
        elif testcase["action"] == "passed":
            if prev_testcase["action"] == "failure" or prev_testcase["regression"]:
                testcase["successfix"] = True
                testsuite2["successfixes"] += 1
    return testsuite2
