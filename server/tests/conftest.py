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
import pytest
import server.app
import server.tests.utils as utils

import sqlalchemy
import sqlalchemy_utils.functions


@pytest.fixture(scope="session")
def app(request):
    conf = server.app.generate_conf()
    db_uri = conf['SQLALCHEMY_DATABASE_URI']

    if not sqlalchemy_utils.functions.database_exists(db_uri):
        sqlalchemy_utils.functions.create_database(db_uri)

        request.addfinalizer(
            lambda: sqlalchemy_utils.functions.drop_database(db_uri)
        )

        engine = sqlalchemy.create_engine(db_uri)
        sql_file_path = "db_schema/dci-control-server.sql"
        with engine.begin() as conn, open(sql_file_path) as f:
            conn.execute(f.read())

    app = server.app.create_app(conf)
    app.testing = True
    return app


@pytest.fixture(autouse=True)
def db_provisioning(request, app):
    session = app._DCI_MODEL.get_session()
    with open("db_schema/dci-control-server-test.sql") as f:
        session.execute(f.read())
    session.commit()

    def fin():
        session.execute("DELETE FROM users")
        session.execute("DELETE FROM user_roles")
        session.execute("DELETE FROM user_remotecis")

        session.execute("DELETE FROM tests")
        session.execute("DELETE FROM teams")
        session.execute("DELETE FROM roles")
        session.execute("DELETE FROM remotecis")
        session.execute("DELETE FROM jobstates")
        session.execute("DELETE FROM jobdefinition_components")
        session.execute("DELETE FROM jobdefinitions")

        session.execute("DELETE FROM jobs")
        session.execute("DELETE FROM files")
        session.execute("DELETE FROM componenttypes")
        session.execute("DELETE FROM components")
        session.commit()

    request.addfinalizer(fin)


@pytest.fixture
def admin(app):
    return utils.generate_client(app, ('admin', 'admin'))


@pytest.fixture
def partner(app):
    return utils.generate_client(app, ('partner', 'partner'))


@pytest.fixture
def unauthorized(app):
    return utils.generate_client(app, ('admin', 'bob'))
