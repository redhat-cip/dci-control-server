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


import uuid

from dci.identity import Identity


def test_identity():

    teams = [uuid.uuid4()]

    super_admin_user = {'role_label': 'SUPER_ADMIN'}
    assert Identity(super_admin_user, []).is_super_admin() is True
    assert Identity(super_admin_user, []).is_in_team(None) is True

    product_owner_user = {'role_label': 'PRODUCT_OWNER'}
    assert Identity(product_owner_user, []).is_product_owner() is True
    assert Identity(product_owner_user, teams). \
        is_team_product_owner(teams[0]) is True
    assert Identity(super_admin_user, []).is_in_team(None) is False

    admin_user = {'role_label': 'ADMIN'}
    assert Identity(admin_user, []).is_admin() is True
    assert Identity(admin_user, teams).is_team_admin(teams[0]) is True
    assert Identity(super_admin_user, []).is_in_team(None) is False

    user = {'role_label': 'USER'}
    assert Identity(user, []).is_regular_user() is True
    assert Identity(user, teams).is_in_team(teams[0]) is True
    assert Identity(super_admin_user, []).is_in_team(None) is False
