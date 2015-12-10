# -*- encoding: utf-8 -*-
#
# Copyright 2015 Red Hat, Inc.
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

from dci.server import auth
from dci.server.db import models


def provision(db_conn):
    def db_insert(model_item, **kwargs):
        query = model_item.insert().values(**kwargs)
        return db_conn.execute(query).inserted_primary_key[0]

    # Create teams
    team_admin_id = db_insert(models.TEAMS, name='admin')
    company_a_id = db_insert(models.TEAMS, name='company_a')
    company_b_id = db_insert(models.TEAMS, name='company_b')
    team_user_id = db_insert(models.TEAMS, name='user')

    # Create users
    user_pw_hash = auth.hash_password('user')
    db_insert(models.USERS,
              name='user',
              role='user',
              password=user_pw_hash,
              team_id=team_user_id)

    user_admin_pw_hash = auth.hash_password('user_admin')
    db_insert(models.USERS,
              name='user_admin',
              role='admin',
              password=user_admin_pw_hash,
              team_id=team_user_id)

    admin_pw_hash = auth.hash_password('admin')
    admin_user_id = db_insert(models.USERS,
                              name='admin',
                              role='admin',
                              password=admin_pw_hash,
                              team_id=team_admin_id)

    company_a_pw_hash = auth.hash_password('company_a_user')
    company_a_user_id = db_insert(models.USERS,
                                  name='company_a_user',
                                  password=company_a_pw_hash,
                                  team_id=company_a_id)

    company_b_pw_hash = auth.hash_password('company_b_user')
    company_b_user_id = db_insert(models.USERS,
                                  name='company_b_user',
                                  password=company_b_pw_hash,
                                  team_id=company_b_id)

    # Create roles
    role_admin_id = db_insert(models.ROLES, name='admin')
    role_partner_id = db_insert(models.ROLES, name='partner')

    # Create user_roles
    db_insert(models.JOIN_USERS_ROLES, user_id=admin_user_id,
              role_id=role_admin_id)
    db_insert(models.JOIN_USERS_ROLES, user_id=admin_user_id,
              role_id=role_partner_id)
    db_insert(models.JOIN_USERS_ROLES, user_id=company_a_user_id,
              role_id=role_partner_id)
    db_insert(models.JOIN_USERS_ROLES, user_id=company_b_user_id,
              role_id=role_partner_id)
