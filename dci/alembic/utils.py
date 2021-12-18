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

from os import path

from alembic import command
from alembic import config

from dci import alembic as dci_alembic


def generate_conf():
    dci_alembic_path = path.dirname(path.abspath(dci_alembic.__file__))
    alembic_cfg_path = path.join(dci_alembic_path, "alembic.ini")

    return config.Config(alembic_cfg_path)


def sync():
    # then, load the Alembic configuration and generate the
    # version table if its the first run. Upgrading to the most
    # recent rev
    command.upgrade(generate_conf(), "head")
