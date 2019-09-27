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


def team_has_access_to_a_topic(team_id, product_id, topic_id):
    with flask.g.db_conn.begin():
        query = (
            sql.select([models.JOINS_TOPICS_TEAMS.c.topic_id])
            .select_from(
                models.JOINS_TOPICS_TEAMS.join(models.TOPICS).join(models.TEAMS)
            )
            .where(
                sql.and_(
                    models.TOPICS.c.state == "active",
                    models.TEAMS.c.state == "active",
                    models.JOINS_TOPICS_TEAMS.c.team_id == team_id,
                    models.TOPICS.c.id == topic_id,
                )
            )
        )
        result = flask.g.db_conn.execute(query)
        if result.rowcount > 0:
            return True
        query = (
            sql.select([models.JOIN_PRODUCTS_TEAMS.c.product_id])
            .select_from(
                models.JOIN_PRODUCTS_TEAMS.join(models.PRODUCTS)
                .join(models.TEAMS)
                .join(models.TOPICS)
            )
            .where(
                sql.and_(
                    models.PRODUCTS.c.state == "active",
                    models.TEAMS.c.state == "active",
                    models.JOIN_PRODUCTS_TEAMS.c.team_id == team_id,
                    models.PRODUCTS.c.id == product_id,
                    models.TOPICS.c.export_control == True,  # noqa
                )
            )
        )
        result = flask.g.db_conn.execute(query)
        return result.rowcount > 0
