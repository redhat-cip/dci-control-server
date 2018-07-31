# -*- encoding: utf-8 -*-
#
# Copyright (C) 2018 Red Hat, Inc
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


def test_all_routes_are_in_roles(app):
    for rule in app.url_map.iter_rules():
        endpoint = rule.endpoint.replace('api_v1.', '')
        if endpoint in ["static", "index"]:
            break
        assert endpoint in ROLES


def test_all_purge_methods_are_only_accessible_to_super_admin():
    for endpoint, roles in ROLES.items():
        if 'purge' in endpoint:
            assert len(roles) == 1
            assert roles[0] == SUPER_ADMIN[0]
