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

from dci.identity import Identity


all_teams = [{'id': UUID('eaa68feb-0e23-4dee-9737-7538af531024'),
              'parent_id': None},
             {'id': UUID('2975580b-1915-41b7-9672-c16ccbcc6fc1'),
              'parent_id': None},
             {'id': UUID('66e06983-a7e4-43be-b7ae-33ae80bcf327'),
              'parent_id': None},
             {'id': UUID('2d89a1ad-0638-4738-940d-166c6a8105ec'),
              'parent_id': UUID('66e06983-a7e4-43be-b7ae-33ae80bcf327')},
             {'id': UUID('894c7af1-f90f-48dd-8276-fbc4bfa80371'),
              'parent_id': UUID('66e06983-a7e4-43be-b7ae-33ae80bcf327')}]


def identity_factory(is_user=False, is_product_owner=False,
                     is_super_admin=False, is_read_only_user=False):
    user_info = {
        'id': '12368feb-0e23-4dee-9737-7538af531234',
        'password': 'password',
        'name': 'name',
        'fullname': 'fullname',
        'timezone': 'UTC',
        'email': 'user@email.com',
        'etag': '2975580b-1915-41b7-9672-c16ccbcc1234',
        'is_super_admin': is_super_admin,
        'is_read_only_user': is_read_only_user
    }

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
        team_name = 'product_owner_team'
        user_info['teams'] = {
            UUID('66e06983-a7e4-43be-b7ae-33ae80bcf327'): {
                'team_name': team_name,
                'parent_id': None,
                'role': 'USER'
            }
        }
    elif is_user:
        team_name = 'user'
        user_info['teams'] = {
            UUID('894c7af1-f90f-48dd-8276-fbc4bfa80371'): {
                'team_name': team_name,
                'parent_id': UUID('66e06983-a7e4-43be-b7ae-33ae80bcf327'),
                'role': 'USER'
            },
            UUID('2d89a1ad-0638-4738-940d-166c6a8105ec'): {
                'team_name': team_name,
                'parent_id': UUID('66e06983-a7e4-43be-b7ae-33ae80bcf327'),
                'role': 'USER'
            }
        }
    elif is_read_only_user:
        user_info['teams'] = {
            UUID('12347af1-f90f-48dd-8276-fbc4bfa81234'): {
                'team_name': 'internal',
                'parent_id': None,
                'role': 'READ_ONLY_USER'
            }
        }

    return Identity(user_info, all_teams)


def test_is_super_admin():
    super_admin = identity_factory(is_super_admin=True)
    assert super_admin.is_super_admin()


def test_is_not_super_admin():
    assert identity_factory(is_user=True).is_not_super_admin()


def test_is_product_owner():
    product_owner = identity_factory(is_product_owner=True)
    assert product_owner.is_product_owner(
        '894c7af1-f90f-48dd-8276-fbc4bfa80371')


def test_is_not_product_owner():
    assert identity_factory(is_product_owner=True).is_not_product_owner(
        'eaa68feb-0e23-4dee-9737-7538af531024')


def test_is_feeder():
    user_info = {
        'id': '894c7af1-f90f-48dd-8276-fbc4bfa80371',
        'api_secret': 'secret',
        'teams': {
            UUID('eaa68feb-0e23-4dee-9737-7538af531024'): {
                'team_name': 'team_name',
                'parent_id': UUID('66e06983-a7e4-43be-b7ae-33ae80bcf327'),
                'role': 'FEEDER'
            }
        }
    }
    user = Identity(user_info, [])
    assert user.is_feeder(team_id='eaa68feb-0e23-4dee-9737-7538af531024')


def test_is_remoteci():
    user_info = {
        'id': '894c7af1-f90f-48dd-8276-fbc4bfa80371',
        'api_secret': 'secret',
        'teams': {
            UUID('eaa68feb-0e23-4dee-9737-7538af531024'): {
                'team_name': 'team_name',
                'parent_id': UUID('66e06983-a7e4-43be-b7ae-33ae80bcf327'),
                'role': 'REMOTECI'
            }
        }
    }
    user = Identity(user_info, [])
    assert user.is_remoteci(team_id='eaa68feb-0e23-4dee-9737-7538af531024')


def test_user_is_in_team():
    user = identity_factory(is_user=True)
    assert user.is_in_team(team_id='894c7af1-f90f-48dd-8276-fbc4bfa80371')
    assert user.is_in_team(team_id='2d89a1ad-0638-4738-940d-166c6a8105ec')


def test_user_is_not_in_team():
    user = identity_factory(is_user=True)
    assert user.is_not_in_team(team_id='eaa68feb-0e23-4dee-9737-7538af531024')
    assert user.is_not_in_team(team_id='2975580b-1915-41b7-9672-c16ccbcc6fc1')


def test_super_admin_is_in_all_teams():
    super_admin = identity_factory(is_super_admin=True)

    for team in all_teams:
        assert super_admin.is_in_team(team_id=str(team['id']))


def test_super_admin_is_product_owner_of_all_teams():
    super_admin = identity_factory(is_super_admin=True)

    for team in all_teams:
        assert super_admin.is_product_owner(team_id=str(team['id']))


def test_product_owner_is_in_child_teams():
    product_owner = identity_factory(is_product_owner=True)
    assert product_owner.is_in_team(
        '894c7af1-f90f-48dd-8276-fbc4bfa80371')
    assert product_owner.is_in_team(
        '2d89a1ad-0638-4738-940d-166c6a8105ec')


def test_parent_teams():
    user = identity_factory(is_user=True)
    assert (set([UUID('66e06983-a7e4-43be-b7ae-33ae80bcf327')]) ==
            user.parent_teams_ids)


def test_teams_ids():
    user = identity_factory(is_user=True)
    assert (set([UUID('894c7af1-f90f-48dd-8276-fbc4bfa80371'),
                 UUID('2d89a1ad-0638-4738-940d-166c6a8105ec')]) == set(user.teams_ids))  # noqa


def test_teams_ids_sso_user():
    user = identity_factory(is_read_only_user=True)
    assert user.is_read_only_user()
