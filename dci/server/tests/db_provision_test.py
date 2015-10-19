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

from server.db import models_core

import bcrypt


def provision(db_conn):
    def db_insert(model_item, **kwargs):
        query = model_item.insert().values(**kwargs)
        return db_conn.execute(query).inserted_primary_key[0]

    # Create teams
    db_insert(models_core.TEAMS, name='admin')
    company_a_id = db_insert(models_core.TEAMS, name='company_a')
    company_b_id = db_insert(models_core.TEAMS, name='company_b')

    # Create users
    admin_password = bcrypt.hashpw('admin'.encode('utf-8'),
                                   bcrypt.gensalt()).decode('utf-8')
    admin_user_id = db_insert(models_core.USERS,
                              name='admin',
                              password=admin_password,
                              team_id=company_a_id)

    company_a_password = bcrypt.hashpw('company_a_user'.encode('utf-8'),
                                       bcrypt.gensalt()).decode('utf-8')
    company_a_user_id = db_insert(models_core.USERS,
                                  name='company_a_user',
                                  password=company_a_password,
                                  team_id=company_a_id)

    company_b_password = bcrypt.hashpw('company_b_user'.encode('utf-8'),
                                       bcrypt.gensalt()).decode('utf-8')
    company_b_user_id = db_insert(models_core.USERS,
                                  name='company_b_user',
                                  password=company_b_password,
                                  team_id=company_b_id)

    # Create roles
    role_admin_id = db_insert(models_core.ROLES, name='admin')
    role_partner_id = db_insert(models_core.ROLES, name='partner')

    # Create user_roles
    db_insert(models_core.JOIN_USERS_ROLES, user_id=admin_user_id,
              role_id=role_admin_id)
    db_insert(models_core.JOIN_USERS_ROLES, user_id=admin_user_id,
              role_id=role_partner_id)
    db_insert(models_core.JOIN_USERS_ROLES, user_id=company_a_user_id,
              role_id=role_partner_id)
    db_insert(models_core.JOIN_USERS_ROLES, user_id=company_b_user_id,
              role_id=role_partner_id)
