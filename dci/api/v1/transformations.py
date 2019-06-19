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


def parse_testcase(root):
    return {
        "name": root.attrib.get("name", ""),
        "classname": root.attrib.get("classname", ""),
        "regression": False,
        "successfix": False,
        "time": float(root.attrib.get("time", 0)),
    }


def parse_action(root):
    return {
        "message": root.get("message", ""),
        "value": root.text,
        "action": root.tag
        if root.tag not in ["system-out", "system-err"]
        else "passed",
        "type": root.get("type", ""),
    }


def parse_element(root):
    testcase = {"action": "passed", "message": "", "type": "", "value": ""}
    testcase.update(parse_testcase(root))
    if len(root) > 0:
        action = parse_action(root[0])
        testcase.update(action)
    return testcase


def junit2dict(file_descriptor):
    if not file_descriptor.read(1):
        return {}
    file_descriptor.seek(0)
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
        for event, element in ElementTree.iterparse(
            file_descriptor, events=("start", "end")
        ):
            if event == "start" and element.tag == "testcase":
                testcase = parse_element(element)
                results["total"] += 1
                test_duration += timedelta(seconds=float(testcase["time"]))
                if testcase["action"] == "skipped":
                    results["skips"] += 1
                if testcase["action"] == "error":
                    results["errors"] += 1
                if testcase["action"] == "failure":
                    results["failures"] += 1
                results["testscases"].append(testcase)
            else:
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
        logger.exception(e)
    return results


def add_regressions_and_successfix_to_tests(testsuite1, testsuite2):
    # dict from testcase's name to each testcase itself for fast access
    testscases1_map = dict()
    for testcase in testsuite1["testscases"]:
        testcase["name"] = testcase["name"].split("[")[0]
        testname = "%s:%s" % (testcase["classname"], testcase["name"])
        testscases1_map[testname] = testcase

    for testcase in testsuite2["testscases"]:
        testcase["name"] = testcase["name"].split("[")[0]
        testname = "%s:%s" % (testcase["classname"], testcase["name"])
        # this is a new test then ignore it
        if testname not in testscases1_map:
            continue
        prev_testcase = testscases1_map[testname]
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


def add_known_issues_to_tests(testsuite, tests_to_issues):
    for testcase in testsuite["testscases"]:
        if testcase["action"] == "failure":
            testcase["name"] = testcase["name"].split("[")[0]
            testname = "%s:%s" % (testcase["classname"], testcase["name"])
            if testname in tests_to_issues:
                testcase["issues"] = tests_to_issues[testname]
            else:
                testcase["issues"] = []
    return testsuite
