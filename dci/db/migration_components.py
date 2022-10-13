# -*- encoding: utf-8 -*-
#
# Copyright 2023 Red Hat, Inc.
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
import re


def _get_version_delimiter(component_name):
    delimiter = None
    for c in [":", "@", " "]:
        if c in component_name:
            delimiter = c
            break
    return delimiter


def _is_sha1(s):
    pattern = r"^[a-fA-F0-9]{40}$"
    return bool(re.match(pattern, s))


def get_new_component_info(component):
    name = component["name"]
    canonical_project_name = component["canonical_project_name"]

    name_is_a_sha1 = _is_sha1(name)

    component_name = (
        canonical_project_name
        if canonical_project_name
        and (
            "OpenShift" in canonical_project_name
            or name in canonical_project_name
            or name_is_a_sha1
        )
        else name
    )

    version = ""
    delimiter = _get_version_delimiter(component_name)
    if delimiter:
        version = component_name.rsplit(delimiter, 1)[1]

    for short_name in ["RHOS-", "RHEL-"]:
        if short_name in component_name:
            version = component_name.rsplit(short_name, 1)[-1]
            break

    if "dci-openshift-app-agent" in component_name:
        component_name = canonical_project_name

    if canonical_project_name and "OpenShift" in canonical_project_name:
        version = name

    return {
        "display_name": component_name,
        "version": version,
        "uid": name if name_is_a_sha1 else "",
    }
