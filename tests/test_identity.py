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


from dci.identity import Identity


def test_identity():

    teams = ['90b89be5-141d-4866-bb4d-248694d95445']

    super_admin_user = {'role_name': 'SUPER_ADMIN'}
    assert Identity(super_admin_user, []).is_super_admin() is True

    product_owner_user = {'role_name': 'PRODUCT_OWNER'}
    assert Identity(product_owner_user, []).is_product_owner() is True
    assert Identity(product_owner_user, teams). \
        is_team_product_owner('90b89be5-141d-4866-bb4d-248694d95445') is True

    admin_user = {'role_name': 'ADMIN'}
    assert Identity(admin_user, []).is_admin() is True
    assert Identity(admin_user, teams). \
        is_team_admin('90b89be5-141d-4866-bb4d-248694d95445') is True

    user = {'role_name': 'USER'}
    assert Identity(user, []).is_regular_user() is True
    assert Identity(user, teams). \
        is_in_team('90b89be5-141d-4866-bb4d-248694d95445') is True
