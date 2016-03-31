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

from dci.api.v1 import transformations

import json


def test_junitojson_valid():
    junit = """
<testsuite errors="0" failures="0" name="junittojson" skips="1"
           tests="3" time="46.050">
<properties>
  <property name="x" value="y" />
  <property name="a" value="b" />
</properties>
<testcase classname="" file="test-requirements.txt"
          name="test-requirements.txt" time="0.0109479427338">
    <skipped message="all tests skipped by +SKIP option"
             type="pytest.skip">Skipped for whatever reasons</skipped>
</testcase>
<testcase classname="tests.test_app" file="tests/test_app.py" line="26"
          name="test_cors_preflight" time="2.91562318802"/>
<testcase classname="tests.test_app" file="tests/test_app.py" line="42"
          name="test_cors_headers" time="0.574683904648"/>
</testsuite>
"""

    result = {
        'content': junit,
        'mime': 'application/junit'
    }

    result = transformations.junittojson(result)
    result = json.loads(result['content'])

    assert result['name'] == 'junittojson'
    assert result['total'] == '3'
    assert len(result['properties']) == 2

def test_junitojson_invalid():
    junit = """
<testsuite errors="0" failures="0" name="junittojson" skips="1"
           tests="3" time="46.050">
<properties>
  <property name="x" value="y" />
  <property name="a" value="b" />
</properties>
<testcase classname="" file="test-requirements.txt"
          name="test-requirements.txt" time="0.0109479427338">
    <skipped message="all tests skipped by +SKIP option"
             type="pytest.skip">Skipped for whatever reasons</skipped>
<testcase classname="tests.test_app" file="tests/test_app.py" line="26"
          name="test_cors_preflight" time="2.91562318802"/>
<testcase classname="tests.test_app" file="tests/test_app.py" line="42"
          name="test_cors_headers" time="0.574683904648"/>
</testsuite>
"""

    result = {
        'content': junit,
        'mime': 'application/junit'
    }

    result = transformations.junittojson(result)
    result = json.loads(result['content'])

    assert 'XMLSyntaxError' in result['error']

def test_junitojson_empty():

    result = {
        'content': '',
        'mime': 'application/junit'
    }

    result = transformations.junittojson(result)
    result = json.loads(result['content'])

    assert result == {}
