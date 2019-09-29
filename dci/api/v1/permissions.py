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


def team_has_access_to_a_topic(team_id, product_id, topic_id):
    with flask.g.db_conn.begin():
        # check if the topic is export control ready or if the user's team
        # is associated to the topic
        def get_team_topic_ids(team_id):
            """Retrieve the list of topics ids associated to the given team."""
            query = (sql.select([models.JOINS_TOPICS_TEAMS.c.topic_id])
                    .select_from(
                        models.JOINS_TOPICS_TEAMS.join(
                            models.TOPICS, sql.and_(models.JOINS_TOPICS_TEAMS.c.topic_id == models.TOPICS.c.id,  # noqa
                                                    models.TOPICS.c.state == 'active'))  # noqa
                    ).where(models.JOINS_TOPICS_TEAMS.c.team_id == team_id))
            rows = flask.g.db_conn.execute(query).fetchall()
            return [str(row[0]) for row in rows]

        team_topic_ids = get_team_topic_ids(team_id)

        q_get_topic_team = (
            sql.select([models.TOPICS])
            .where(sql.or_(
                    models.TOPICS.c.id.in_(team_topic_ids),
                    sql.and_(
                        models.TOPICS.c.export_control == True,  # noqa
                        models.TOPICS.c.id == topic_id
                    )
                )
            ))

        result = flask.g.db_conn.execute(q_get_topic_team)
        return result.rowcount > 0
