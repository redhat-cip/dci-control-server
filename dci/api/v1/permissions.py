# -*- coding: utf-8 -*-
#
# Copyright (C) Red Hat, Inc
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

from dci.db import models

import flask
from sqlalchemy import sql


def is_users_team_associated_with_the_product(team_id, product_id):
    q_get_product_team = (
        sql.select([models.JOIN_PRODUCTS_TEAMS])
        .select_from(
            models.JOIN_PRODUCTS_TEAMS.join(models.PRODUCTS).join(models.TEAMS)
        )
        .where(
            sql.and_(
                models.JOIN_PRODUCTS_TEAMS.c.team_id == team_id,
                models.PRODUCTS.c.state == "active",
                models.TEAMS.c.state == "active",
                models.PRODUCTS.c.id == product_id,
            )
        )
    )
    result = flask.g.db_conn.execute(q_get_product_team)
    return result.rowcount > 0


def is_users_team_associated_with_the_topic(team_id, topic_id):
    team_in_topic = sql.and_(
        models.TOPICS.c.state == "active",
        models.TEAMS.c.state == "active",
        models.JOINS_TOPICS_TEAMS.c.team_id == team_id,
        models.JOINS_TOPICS_TEAMS.c.topic_id == topic_id,
    )
    topic_export_control_ready = sql.and_(
        models.TOPICS.c.state == "active",
        models.TOPICS.c.export_control == True,  # noqa
        models.TOPICS.c.id == topic_id,
    )
    q_get_topic_team = (
        sql.select([models.JOINS_TOPICS_TEAMS.c.topic_id])
        .select_from(models.JOINS_TOPICS_TEAMS.join(models.TOPICS).join(models.TEAMS))
        .where(sql.or_(team_in_topic, topic_export_control_ready))
    )
    result = flask.g.db_conn.execute(q_get_topic_team)
    return result.rowcount > 0


def team_has_access_to_a_topic(team_id, product_id, topic_id):
    if not is_users_team_associated_with_the_product(team_id, product_id):
        return False
    return is_users_team_associated_with_the_topic(team_id, topic_id)
