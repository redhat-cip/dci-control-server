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

import dci.server.app
from dci.server.db import models_core
from dci.server.tests import db_provision_test
import dci.server.tests.utils as utils

import pytest
import sqlalchemy
import sqlalchemy_utils.functions


@pytest.fixture(scope='session')
def engine(request):
    conf = dci.server.app.generate_conf()
    db_uri = conf['SQLALCHEMY_DATABASE_URI']

    engine = sqlalchemy.create_engine(db_uri)

    def del_db():
        if sqlalchemy_utils.functions.database_exists(db_uri):
            sqlalchemy_utils.functions.drop_database(db_uri)

    del_db()
    request.addfinalizer(del_db)
    sqlalchemy_utils.functions.create_database(db_uri)

    with engine.begin() as conn:
        conn.execute(models_core.pg_gen_uuid)
    models_core.metadata.create_all(engine)
    return engine


@pytest.fixture
def app(engine):
    app = dci.server.app.create_app(dci.server.app.generate_conf())
    app.testing = True
    app.engine = engine
    return app


@pytest.fixture
def db_clean(request, app):
    def fin():
        for table in reversed(models_core.metadata.sorted_tables):
            app.engine.execute(table.delete())
    request.addfinalizer(fin)


@pytest.fixture
def db_provisioning(app, db_clean):
    with app.engine.begin() as conn:
        db_provision_test.provision(conn)


@pytest.fixture
def admin(app, db_provisioning):
    return utils.generate_client(app, ('admin', 'admin'))


@pytest.fixture
def company_a_user(app, db_provisioning):
    return utils.generate_client(app, ('company_a_user', 'company_a_user'))


@pytest.fixture
def company_b_user(app, db_provisioning):
    return utils.generate_client(app, ('company_b_user', 'company_b_user'))


@pytest.fixture
def unauthorized(app, db_provisioning):
    return utils.generate_client(app, ('admin', 'bob'))
