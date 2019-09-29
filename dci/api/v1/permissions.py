# -*- encoding: utf-8 -*-
#
# Copyright Red Hat, Inc.
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

from dci.db import models

import flask
from sqlalchemy import sql


def is_team_associated_to_product(team_id, product_id):
    q_get_product_team = (
        sql.select([models.JOIN_PRODUCTS_TEAMS])
        .where(
            models.JOIN_PRODUCTS_TEAMS.c.team_id == team_id,
        )
    )
    result = flask.g.db_conn.execute(q_get_product_team)
    return result.rowcount > 0


def is_team_associated_to_topic(team_id, topic_id):
    q_get_topic__team = (
        sql.select([models.JOINS_TOPICS_TEAMS])
        .where(
            models.JOINS_TOPICS_TEAMS.c.team_id == team_id,
        )
    )
    result = flask.g.db_conn.execute(q_get_topic__team)
    return result.rowcount > 0
