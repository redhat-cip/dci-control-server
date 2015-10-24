#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Red Hat, Inc
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
"""
This module synchronize the database with the most up to
date schema through Alembic.
"""

from os import path

from alembic import command
from alembic import config

from dci.server import app
from dci.server.db import models_core


def main():
    # Create model from application database schema
    app_conf = app.generate_conf()
    sa_engine = app.get_engine(app_conf)

    with sa_engine.begin() as conn:
            conn.execute(models_core.pg_gen_uuid)
    models_core.metadata.create_all(sa_engine)

    # then, load the Alembic configuration and generate the
    # version table, "stamping" it with the most recent rev:
    cmd_path = path.dirname(path.abspath(__file__))
    alembic_cfg_path = "%s/%s" % (path.dirname(cmd_path),
                                  'alembic/alembic.ini')
    alembic_cfg = config.Config(alembic_cfg_path)
    command.stamp(alembic_cfg, "head")

if __name__ == '__main__':
    main()
