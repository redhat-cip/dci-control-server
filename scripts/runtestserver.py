#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Red Hat, Inc
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

from dci import app
from dci import auth
from dci import dci_config
from dci.db import models

import sqlalchemy
import sqlalchemy_utils.functions


def provision(db_conn):
    def db_insert(model_item, **kwargs):
        query = model_item.insert().values(**kwargs)
        return db_conn.execute(query).inserted_primary_key[0]

    user_pw_hash = auth.hash_password('user')
    user_admin_pw_hash = auth.hash_password('user_admin')
    admin_pw_hash = auth.hash_password('admin')

    # Create teams
    team_admin_id = db_insert(models.TEAMS, name='admin')
    team_user_id = db_insert(models.TEAMS, name='user')

    # Create users
    db_insert(models.USERS,
              name='user',
              role='user',
              password=user_pw_hash,
              team_id=team_user_id)

    db_insert(models.USERS,
              name='user_admin',
              role='admin',
              password=user_admin_pw_hash,
              team_id=team_user_id)

    db_insert(models.USERS,
              name='admin',
              role='admin',
              password=admin_pw_hash,
              team_id=team_admin_id)


conf = dci_config.generate_conf()
db_uri = conf['SQLALCHEMY_DATABASE_URI']

engine = sqlalchemy.create_engine(db_uri)

if sqlalchemy_utils.functions.database_exists(db_uri):
    sqlalchemy_utils.functions.drop_database(db_uri)

sqlalchemy_utils.functions.create_database(db_uri)

models.metadata.create_all(engine)

with engine.begin() as conn:
    provision(conn)

print(conf)
dci_app = app.create_app(conf)

dci_app.run(dci_app.config['HOST'],
            dci_app.config['PORT'])
