# -*- encoding: utf-8 -*-
#
# Copyright 2017 Red Hat, Inc.
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
from dci.policies import ROLES, SUPER_ADMIN


def _get_endpoints(app):
    endpoints = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static":
            break
        endpoints.append(rule.endpoint.replace('api_v1.', ''))
    return endpoints


def test_all_routes_are_in_roles(app):
    for endpoint in _get_endpoints(app):
        assert endpoint in ROLES


def test_all_purge_methods_are_only_accessible_to_super_admin(app):
    for endpoint in _get_endpoints(app):
        if 'purge' in endpoint:
            assert len(ROLES[endpoint]) == 1
            assert ROLES[endpoint][0] == SUPER_ADMIN[0]
