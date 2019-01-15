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

from uuid import UUID
import pytest

from dci.identity import Identity


def identity_factory(is_user=False, is_product_owner=False,
                     is_super_admin=False, multi_teams=False):
    user_info = {
        'id': '12368feb-0e23-4dee-9737-7538af531234',
        'password': 'password',
        'name': 'name',
        'fullname': 'fullname',
        'timezone': 'UTC',
        'email': 'user@email.com',
        'etag': '2975580b-1915-41b7-9672-c16ccbcc1234',
        'is_super_admin': is_super_admin
    }

    team_name = 'user'
    if is_super_admin:
        team_name = 'admin'
        user_info['teams'] = {
            UUID('2975580b-1915-41b7-9672-c16ccbcc6fc1'): {
                'team_name': team_name,
                'parent_id': None,
                'role': 'USER'
            }
        }
    elif is_product_owner:
        user_info['teams'] = {
            UUID('eaa68feb-0e23-4dee-9737-7538af531024'): {
                'team_name': team_name,
                'parent_id': None,
                'role': 'USER'
            }
        }
    elif is_user:
        user_info['teams'] = {
            UUID('894c7af1-f90f-48dd-8276-fbc4bfa80371'): {
                'team_name': team_name,
                'parent_id': UUID('66e06983-a7e4-43be-b7ae-33ae80bcf327'),
                'role': 'USER'
            }
        }
    all_teams = [{'id': UUID('eaa68feb-0e23-4dee-9737-7538af531024'),
                  'parent_id': None},
                 {'id': UUID('2975580b-1915-41b7-9672-c16ccbcc6fc1'),
                  'parent_id': None},
                 {'id': UUID('66e06983-a7e4-43be-b7ae-33ae80bcf327'),
                  'parent_id': UUID('eaa68feb-0e23-4dee-9737-7538af531024')},
                 {'id': UUID('894c7af1-f90f-48dd-8276-fbc4bfa80371'),
                  'parent_id': UUID('66e06983-a7e4-43be-b7ae-33ae80bcf327')}]

    return Identity(user_info, all_teams)


def test_is_super_admin():
    super_admin = identity_factory(is_super_admin=True)
    assert super_admin.is_super_admin()


def test_is_not_super_admin():
    assert identity_factory(is_user=True).is_not_super_admin()


def test_is_product_owner():
    product_owner = identity_factory(is_product_owner=True)
    assert product_owner.is_product_owner(
        '66e06983-a7e4-43be-b7ae-33ae80bcf327')


def test_is_not_product_owner():
    assert identity_factory(is_product_owner=True).is_not_product_owner(
        '894c7af1-f90f-48dd-8276-fbc4bfa80371')


def loltest_is_feeder():
    assert False


def loltest_is_remoteci():
    assert False


def test_user_is_not_in_team():
    user = identity_factory(is_user=True)
    assert user.is_in_team(team_id='894c7af1-f90f-48dd-8276-fbc4bfa80371')
    assert user.is_not_in_team(team_id='2975580b-1915-41b7-9672-c16ccbcc6fc1')


def test_super_admin_is_in_all_teams():
    super_admin = identity_factory(is_super_admin=True)
        
    assert super_admin.is_in_team(
        team_id='eaa68feb-0e23-4dee-9737-7538af531024')
    assert super_admin.is_in_team(
        team_id='2975580b-1915-41b7-9672-c16ccbcc6fc1')
    assert super_admin.is_in_team(
        team_id='66e06983-a7e4-43be-b7ae-33ae80bcf327')
    assert super_admin.is_in_team(
        team_id='66e06983-a7e4-43be-b7ae-33ae80bcf327')


def test_product_owner_is_in_child_teams():
    product_owner = identity_factory(is_product_owner=True)
    assert product_owner.is_in_team(
        '66e06983-a7e4-43be-b7ae-33ae80bcf327')


def loltest_filter_teams():
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


def loltest_product_team_id_root_team(teams):
    user = Identity({'role_label': 'ADMIN', 'team_id': 'admin'}, teams)
    assert user.product_team_id is None


def loltest_product_team_id_product_team(teams):
    user = Identity({'role_label': 'ADMIN', 'team_id': 'openstack'}, teams)
    assert user.product_team_id == 'openstack'


def loltest_product_team_id_children_team(teams):
    user = Identity({'role_label': 'ADMIN', 'team_id': 'partner3'}, teams)
    assert user.product_team_id == 'openstack'


def loltest_teams_ids(teams):
    user = Identity({'role_label': 'ADMIN', 'team_id': 'partner3'}, teams)
    assert sorted(user.teams_ids) == sorted(['partner3', 'partner4'])


def loltest_teams_ids_sso_user(teams):
    user = Identity({'role_label': 'READ_ONLY_USER', 'team_id': None}, teams)
    assert len(user.teams_ids) == 0
