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


import server.app
from server.db import models_core
from server.tests import db_provision_test
import server.tests.utils as utils

import pytest
import sqlalchemy
import sqlalchemy_utils.functions


@pytest.fixture(scope="session")
def app(request):
    conf = server.app.generate_conf()
    db_uri = conf['SQLALCHEMY_DATABASE_URI']

    engine = sqlalchemy.create_engine(db_uri)
    if not sqlalchemy_utils.functions.database_exists(db_uri):
        sqlalchemy_utils.functions.create_database(db_uri)

        request.addfinalizer(
            lambda: sqlalchemy_utils.functions.drop_database(db_uri)
        )

        with engine.begin() as conn:
            conn.execute(models_core.pg_gen_uuid)

        models_core.metadata.create_all(engine)

    app = server.app.create_app(conf)
    app.testing = True
    app.engine = engine
    return app


@pytest.fixture(autouse=True)
def db_provisioning(request, app):
    with app.engine.begin() as conn:
        db_provision_test.provision(conn)

    def fin():
        for tbl in reversed(app._DCI_MODEL.Base.metadata.sorted_tables):
            app._DCI_MODEL.engine.execute(tbl.delete())

    request.addfinalizer(fin)


@pytest.fixture
def admin(app):
    return utils.generate_client(app, ('admin', 'admin'))


@pytest.fixture
def company_a_user(app):
    return utils.generate_client(app, ('company_a_user', 'company_a_user'))


@pytest.fixture
def company_b_user(app):
    return utils.generate_client(app, ('company_b_user', 'company_b_user'))


@pytest.fixture
def unauthorized(app):
    return utils.generate_client(app, ('admin', 'bob'))
