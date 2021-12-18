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

import dci.alembic.utils
import dci.db.models as models


def test_cors_preflight(admin):
    headers = {
        "Origin": "http://foo.example",
        "Access-Control-Request-Method": "POST",
    }
    resp = admin.options("/api/v1", headers=headers)
    headers = resp.headers

    allowed_headers = "Authorization, Content-Type, If-Match, ETag, " "X-Requested-With"

    assert resp.status_code == 200
    assert headers["Access-Control-Allow-Headers"] == allowed_headers
    assert headers["Access-Control-Allow-Origin"] == "*"
    assert headers["Access-Control-Allow-Methods"] == "GET, POST, PUT, DELETE"


def test_cors_headers(admin):
    resp = admin.get("/api/v1/jobs")
    assert resp.headers["Access-Control-Allow-Origin"] == "*"


def test_db_migration(engine, delete_db):
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
            connection, target_metadata=models.metadata, compare_type=True
        )

        with context.begin_transaction():
            context.run_migrations()

        diff = alembic.autogenerate.api.compare_metadata(
            context.get_context(), models.metadata
        )

    assert diff == []
