# -*- encoding: utf-8 -*-
#
# Copyright 2015-2016 Red Hat, Inc.
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

JUNIT = """<testsuite errors="0" failures="0" name="pytest" skips="1"
               tests="3" time="46.050">
    <properties>
      <property name="x" value="y" />
      <property name="a" value="b" />
    </properties>
    <testcase classname="classname_1" name="test_1" time="0.0109479427338">
        <failure>test failed</failure>
    </testcase>
    <testcase classname="classname_1" name="test_2" time="0.000">
        <skipped message="skipped">test skipped</skipped>
    </testcase>
    <testcase classname="classname_1" name="test_3" time="2.91562318802"/>
</testsuite>
"""
