# -*- encoding: utf-8 -*-
#
# Copyright 2015-2016 Red Hat, Inc.
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

import alembic.autogenerate
import alembic.environment
import alembic.script
import sqlalchemy_utils.functions

import dci.alembic.utils
import dci.app
from dci import dci_config
from dci.db import models2


def test_cors_preflight(client_admin):
    headers = {
        "Origin": "http://foo.example",
        "Access-Control-Request-Method": "POST",
    }
    resp = client_admin.options("/api/v1", headers=headers)
    headers = resp.headers

    allowed_headers = (
        "Authorization, Content-Type, If-Match, ETag, X-Requested-With, X-Dci-Team-Id"
    )

    assert resp.status_code == 200
    assert headers["Access-Control-Allow-Headers"] == allowed_headers
    assert headers["Access-Control-Allow-Origin"] == "*"
    assert headers["Access-Control-Allow-Methods"] == "GET, POST, PUT, DELETE"


def test_cors_headers(client_admin):
    resp = client_admin.get("/api/v1/jobs")
    assert resp.headers["Access-Control-Allow-Origin"] == "*"


def test_db_migration():
    db_uri = (
        "postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}".format(
            db_user=dci_config.CONFIG["DB_USER"],
            db_password=dci_config.CONFIG["DB_PASSWORD"],
            db_host=dci_config.CONFIG["DB_HOST"],
            db_port=dci_config.CONFIG["DB_PORT"],
            db_name="test_db_migration",
        )
    )

    if sqlalchemy_utils.functions.database_exists(db_uri):
        sqlalchemy_utils.functions.drop_database(db_uri)
    sqlalchemy_utils.functions.create_database(db_uri)
    engine = dci_config.get_engine(db_uri)
    config = dci.alembic.utils.generate_conf()
    context = alembic.context
    script = alembic.script.ScriptDirectory.from_config(config)

    env_context = alembic.environment.EnvironmentContext(
        config,
        script,
        destination_rev="head",
        fn=lambda rev, _: script._upgrade_revs("head", rev),
    )

    with env_context, engine.connect() as connection:
        context.configure(
            connection, target_metadata=models2.Base.metadata, compare_type=True
        )

        with context.begin_transaction():
            context.run_migrations()

        diff = alembic.autogenerate.api.compare_metadata(
            context.get_context(), models2.Base.metadata
        )

    assert diff == []
