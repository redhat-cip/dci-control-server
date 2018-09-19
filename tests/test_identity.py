# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Red Hat, Inc
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

import pytest

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
    team = {'id': 'id-1', 'parent_id': None}
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
    assert user.teams_ids[0] == 'abc'


@pytest.fixture
def teams():
    t1 = {'id': 'admin', 'parent_id': None}
    t2 = {'id': 'openstack', 'parent_id': 'admin'}
    t3 = {'id': 'partner1', 'parent_id': 'openstack'}
    t4 = {'id': 'partner2', 'parent_id': 'openstack'}
    t5 = {'id': 'partner3', 'parent_id': 'openstack'}
    t6 = {'id': 'partner4', 'parent_id': 'partner3'}
    t7 = {'id': 'rhel', 'parent_id': 'admin'}
    t8 = {'id': 'partner5', 'parent_id': 'rhel'}
    return [t1, t2, t3, t4, t5, t6, t7, t8]


def test_product_team_id_root_team(teams):
    user = Identity({'role_label': 'ADMIN', 'team_id': 'admin'}, teams)
    assert user.product_team_id is None


def test_product_team_id_product_team(teams):
    user = Identity({'role_label': 'ADMIN', 'team_id': 'openstack'}, teams)
    assert user.product_team_id == 'openstack'


def test_product_team_id_children_team(teams):
    user = Identity({'role_label': 'ADMIN', 'team_id': 'partner3'}, teams)
    assert user.product_team_id == 'openstack'


def test_teams_ids(teams):
    user = Identity({'role_label': 'ADMIN', 'team_id': 'partner3'}, teams)
    assert sorted(user.teams_ids) == sorted(['partner3', 'partner4'])


def test_teams_ids_sso_user(teams):
    user = Identity({'role_label': 'READ_ONLY_USER', 'team_id': None}, teams)
    assert len(user.teams_ids) == 0
