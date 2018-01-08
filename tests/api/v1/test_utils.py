# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Red Hat, Inc
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

from dci.api.v1 import utils


def test_get_regressions_failures():
    jobtest1 = """
<testsuite errors="0" failures="60" name="" tests="2289" time="3385.127">
    <testcase
            classname="Testsuite_1"
            name="test_1"
            time="28.810">
        <failure type="Exception">Traceback</failure>
    </testcase>
    <testcase
            classname="Testsuite1"
            name="test_2"
            time="29.419">
    </testcase>
        <testcase
            classname="Testsuite1"
            name="test_3"
            time="29.419">
    </testcase>
</testsuite>
"""
    jobtest2 = """
<testsuite errors="0" failures="60" name="" tests="2289" time="3385.127">
    <testcase
            classname="Testsuite_1"
            name="test_1"
            time="28.810">
        <failure type="Exception">Traceback</failure>
    </testcase>
    <testcase
            classname="Testsuite1"
            name="test_2"
            time="29.419">
        <failure type="Exception">Traceback</failure>
    </testcase>
    <testcase
            classname="Testsuite1"
            name="test_3"
            time="29.419">
            <failure type="Exception">Traceback</failure>
    </testcase>
</testsuite>
"""
    regressions = utils.get_regressions_failures(jobtest1, jobtest2)
    assert len(regressions) == 2
    assert set(regressions) == set(['test_2', 'test_3'])
