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

from dci.server import app
from dci.server.db import models_core as models

import pytest
import sqlalchemy_utils.functions


@pytest.fixture(scope='session')
def test_app(request):
    conf = app.generate_conf()
    t_app = app.create_app(conf)
    db_uri = conf['SQLALCHEMY_DATABASE_URI']

    def drop_db():
        if sqlalchemy_utils.functions.database_exists(db_uri):
            sqlalchemy_utils.functions.drop_database(db_uri)
    drop_db()
    request.addfinalizer(drop_db)
    sqlalchemy_utils.functions.create_database(db_uri)

    models.metadata.create_all(t_app.engine)
    return t_app


@pytest.fixture(scope='session')
def test_client(test_app):
    test_app.config['TESTING'] = True
    return test_app.test_client()


@pytest.fixture(autouse=True)
def clean_db(request, test_app):
    def clean():
        for table in reversed(models.metadata.sorted_tables):
            test_app.engine.execute(table.delete())
    request.addfinalizer(clean)
