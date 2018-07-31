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

import dci.auth_mechanism as authm


def test_base_mecanism_get_team_and_children_teams():

    teams = [
        {'id': '1', 'parent_id': None},
        {'id': '2', 'parent_id': None},
        {'id': '11', 'parent_id': '1'},
        {'id': '12', 'parent_id': '1'},
        {'id': '111', 'parent_id': '11'},
        {'id': '112', 'parent_id': '11'},
        {'id': '1111', 'parent_id': '111'},
        {'id': '1112', 'parent_id': '111'},
    ]

    assert sorted([team['id'] for team in authm.BaseMechanism.get_team_and_children_teams(teams, '1')]) == sorted(['1', '11', '12', '111', '112', '1111', '1112'])  # noqa

    assert sorted([team['id'] for team in authm.BaseMechanism.get_team_and_children_teams(teams, '111')]) == sorted(['111', '1111', '1112'])  # noqa
