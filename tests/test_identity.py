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
import uuid

from dci.identity import Identity

# == START FIXTURES == 8< -----------------------------------

all_roles = ['ADMIN',
             'SUPER_ADMIN',
             'USER',
             'REMOTECI',
             'PRODUCT_OWNER',
             'FEEDER']


def not_roles(not_these_ones):
    return [role for role in all_roles if role not in (not_these_ones)]


@pytest.fixture
def his_team():
    return uuid.uuid4()


@pytest.fixture
def teams(his_team):
    return [his_team] + [uuid.uuid4() for n in range(5)]


def identity_factory(team_id, teams, role_label):
    return Identity(
        {'team_id': team_id, 'role_label': role_label},
        teams
    )


@pytest.fixture
def user(his_team, teams):
    return identity_factory(his_team, teams, 'USER')


@pytest.fixture
def super_admin(his_team, teams):
    return identity_factory(his_team, teams, 'SUPER_ADMIN')


@pytest.fixture
def admin(his_team, teams):
    return identity_factory(his_team, teams, 'ADMIN')


@pytest.fixture
def product_owner(his_team, teams):
    return identity_factory(his_team, teams, 'PRODUCT_OWNER')


@pytest.fixture
def remoteci(his_team, teams):
    return identity_factory(his_team, teams, 'REMOTECI')


@pytest.fixture
def feeder(his_team, teams):
    return identity_factory(his_team, teams, 'FEEDER')


@pytest.fixture(params=all_roles)
def any_role(request, his_team, teams):
    return identity_factory(his_team, teams, request.param)


@pytest.fixture(params=not_roles('PRODUCT_OWNER'))
def not_product_owner(request, his_team, teams):
    return identity_factory(his_team, teams, request.param)


@pytest.fixture(params=not_roles('SUPER_ADMIN'))
def not_super_admin(request, his_team, teams):
    return identity_factory(his_team, teams, request.param)


@pytest.fixture(params=not_roles(('SUPER_ADMIN', 'PRODUCT_OWNER')))
def not_po_not_sa(request, his_team, teams):
    return identity_factory(his_team, teams, request.param)


@pytest.fixture(params=not_roles('ADMIN'))
def not_admin(request, his_team, teams):
    return identity_factory(his_team, teams, request.param)


@pytest.fixture(params=not_roles('USER'))
def not_user(request, his_team, teams):
    return identity_factory(his_team, teams, request.param)


@pytest.fixture(params=not_roles('REMOTECI'))
def not_remoteci(request, his_team, teams):
    return identity_factory(his_team, teams, request.param)


@pytest.fixture(params=not_roles('FEEDER'))
def not_feeder(request, his_team, teams):
    return identity_factory(his_team, teams, request.param)


# == END FIXTURES == 8< -------------------------------------


def test_filter_teams_on_role_product_owner(product_owner, teams, his_team):
    product_owner.teams = None
    product_owner._filter_teams_on_role(teams)
    assert product_owner.teams == teams


def test_filter_teams_on_role_not_product_owner(not_product_owner, teams,
                                                his_team):
    not_product_owner.teams = None
    not_product_owner._filter_teams_on_role(teams)
    assert not_product_owner.teams == [his_team]


def test_is_in_team_any_role_own_team(any_role, his_team):
    assert any_role.is_in_team(his_team) is True


def test_is_in_team_super_admin_random_yes(super_admin):
    assert super_admin.is_in_team(uuid.uuid4()) is True


def test_is_in_team_super_admin_none(super_admin):
    assert super_admin.is_in_team(None) is True


def test_is_in_team_not_super_admin_none(not_super_admin):
    assert not_super_admin.is_in_team(None) is False


def test_is_in_team_product_owner_own_teams_yes(product_owner, teams):
    for team in teams:
        assert product_owner.is_in_team(team) is True


def test_is_in_team_not_product_owner_own_teams_no(not_po_not_sa, his_team,
                                                   teams):
    for team in teams:
        if team != his_team:
            assert not_po_not_sa.is_in_team(team) is False


def test_is_super_admin_yes(super_admin):
    assert super_admin.is_super_admin() is True


def test_is_super_admin_no(not_super_admin):
    assert not_super_admin.is_super_admin() is False


def test_is_product_owner_yes(product_owner):
    assert product_owner.is_product_owner() is True


def test_is_product_owner_no(not_product_owner):
    assert not_product_owner.is_product_owner() is False


def test_is_team_product_owner_own_team_yes(product_owner):
    assert product_owner.is_team_product_owner(product_owner.team_id) is True


def test_is_team_product_owner_own_teams_yes(product_owner):
    for team_id in product_owner.teams:
        assert product_owner.is_team_product_owner(team_id) is True


def test_is_team_product_owner_random_team_no(any_role):
    assert any_role.is_team_product_owner(uuid.uuid4) is False


def test_is_team_product_owner_own_team_no(not_product_owner):
    assert not_product_owner.is_team_product_owner(
        not_product_owner.team_id) is False


def test_is_team_product_owner_own_teams_no(not_product_owner):
    for team_id in not_product_owner.teams:
        assert not_product_owner.is_team_product_owner(team_id) is False


def test_is_admin_yes(admin):
    assert admin.is_admin() is True


def test_is_admin_no(not_admin):
    assert not_admin.is_admin() is False


def test_is_team_admin_yes(admin):
    assert admin.is_team_admin(admin.team_id) is True


def test_is_team_admin_no(not_admin):
    assert not_admin.is_team_admin(not_admin.team_id) is False


def test_is_team_admin_not_his_team_no(any_role):
    assert any_role.is_team_admin(uuid.uuid4()) is False


def test_is_regular_user_yes(user):
    assert user.is_regular_user() is True


def test_is_regular_user_no(not_user):
    assert not_user.is_regular_user() is False


def test_is_remoteci_yes(remoteci):
    assert remoteci.is_remoteci() is True


def test_is_remoteci_no(not_remoteci):
    assert not_remoteci.is_remoteci() is False


def test_identity_constructor_attrs():
    id_dict = {
        'team_id': uuid.uuid4(),
        'role_label': 'BLAH',
        'foo': 'bar',
        'ooooh': 'donut!'
    }
    identity = Identity(id_dict, [])
    for k, v in id_dict.items():
        assert hasattr(identity, k)


def test_identity_constructor_values():
    id_dict = {
        'team_id': uuid.uuid4(),
        'role_label': 'BLAH',
        'foo': 'bar',
        'ooooh': 'donut!'
    }
    identity = Identity(id_dict, [])
    for k, v in id_dict.items():
        assert getattr(identity, k) == v


def test_identity_constructor___getitem__():
    id_dict = {
        'team_id': uuid.uuid4(),
        'role_label': 'BLAH',
        'foo': 'bar',
        'ooooh': 'donut!'
    }
    identity = Identity(id_dict, [])
    for k, v in id_dict.items():
        assert identity[k] == v
