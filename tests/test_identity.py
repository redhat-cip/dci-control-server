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


import dci.auth_mechanism as authm

from dci.identity import Identity


def identity_factory(role_label):
    user = {'role_label': role_label, 'team_id': 'abc'}
    team = {'id': 'abc', 'parent_id': None}
    return Identity(user, [team])


def test_is_super_admin():
    super_admin = identity_factory('SUPER_ADMIN')
    assert super_admin.is_super_admin()


def test_is_admin():
    admin = identity_factory('ADMIN')
    assert admin.is_admin()


def test_is_product_owner():
    product_owner = identity_factory('PRODUCT_OWNER')
    assert product_owner.is_product_owner()


def test_is_feeder():
    feeder = identity_factory('FEEDER')
    assert feeder.is_feeder()


def test_is_remoteci():
    remoteci = identity_factory('REMOTECI')
    assert remoteci.is_remoteci()


def test_is_regular_user():
    user = identity_factory('USER')
    assert user.is_regular_user()


def test_user_is_not_in_team():
    team = {'id': 'id-1', 'parent_id': 'id-0'}
    user = Identity({'role_label': 'USER', 'team_id': 'id-1'}, [team])
    assert user.is_in_team(team_id='id-1')
    assert user.is_not_in_team(team_id='another_team_id')


def test_super_admin_is_not_in_team_all_teams():
    super_admin = identity_factory('SUPER_ADMIN')
    assert super_admin.is_in_team(team_id='id-1')
    assert super_admin.is_in_team(team_id='id-2')


def test_product_owner_is_not_in_team_all_child_teams():
    product_owner = {'role_label': 'PRODUCT_OWNER', 'team_id': 'abc'}
    teams = [
        {'id': 'abc', 'parent_id': None},
        {'id': 'def', 'parent_id': 'abc'},
        {'id': 'ghi', 'parent_id': None}
    ]
    user = Identity(product_owner, teams)
    assert user.is_in_team(team_id='abc')
    assert user.is_in_team(team_id='def')


def test_filter_teams():
    teams = [
        {'id': 'abc', 'parent_id': None},
        {'id': 'cde', 'parent_id': 'abc'}
    ]
    user = Identity({'role_label': 'USER', 'team_id': 'abc'}, teams)
    assert user.team['id'] == 'abc'
    assert user.team['parent_id'] is None
    # TODO remove user.teams
    assert user.teams[0] == 'abc'
    assert len(user.partner_teams) == 1


def test_filter_teams_with_partner_teams():
    product_owner = {'role_label': 'PRODUCT_OWNER', 'team_id': 'abc'}
    teams = [
        {'id': 'abc', 'parent_id': None},
        {'id': 'def', 'parent_id': 'abc'},
        {'id': 'ghi', 'parent_id': None}
    ]
    teams = authm.BaseMechanism.get_team_and_children_teams(teams, 'abc')

    user = Identity(product_owner, teams)
    assert user.team['id'] == 'abc'
    assert user.team['parent_id'] is None
    assert len(user.partner_teams) == 1
    # TODO remove user.teams
    assert user.teams[0] == 'abc'
    assert user.teams[1] == 'def'


def test_ensure_any_parent_team_member_has_access_to_subteam():
    user = {'role_label': None, 'team_id': 'abc'}
    teams = [
        {'id': 'abc', 'parent_id': None},
        {'id': 'def', 'parent_id': 'abc'},
        {'id': 'ghi', 'parent_id': None}
    ]
    teams = authm.BaseMechanism.get_team_and_children_teams(teams, 'abc')

    user = Identity(user, teams)
    assert user.team['id'] == 'abc'
    assert user.team['parent_id'] is None
    assert len(user.partner_teams) == 1


def test_if_no_team_id_get_team_and_children_teams_return_empty_array():
    teams = [
        {'id': 'abc', 'parent_id': None},
        {'id': 'def', 'parent_id': 'abc'}
    ]
    teams = authm.BaseMechanism.get_team_and_children_teams(teams, None)
    assert len(teams) == 0
