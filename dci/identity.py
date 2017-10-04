# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Red Hat, Inc
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

import flask

from dci.db import models
from sqlalchemy import sql
from dci.api.v1 import utils as v1_utils


class Identity:
    """Class that offers helper methods to simplify permission management
    """

    def __init__(self, user):
        for key in user.keys():
            setattr(self, key, user[key])

        self.teams = self._get_user_teams()
        self.topics = self._get_user_topics()

    # TODO(spredzy): In order to avoid a huge refactor patch, the __getitem__
    # function is overloaded so it behaves like a dict and the code in place
    # can work transparently
    def __getitem__(self, key):
        return getattr(self, key)

    def _get_user_teams(self):
        """Retrieve all the teams that belongs to a user.

        SUPER_ADMIN own all teams.
        PRODUCT_OWNER own all teams attached to a product.
        ADMIN/USER own their own team
        """

        teams = []
        if not self.is_super_admin() and not self.is_product_owner():
            teams = [self.team_id]
        else:
            query = sql.select([models.TEAMS.c.id])
            if self.is_product_owner():
                query = query.where(
                    sql.or_(
                        models.TEAMS.c.parent_id == self.team_id,
                        models.TEAMS.c.id == self.team_id
                    )
                )

            result = flask.g.db_conn.execute(query).fetchall()
            teams = [row[models.TEAMS.c.id] for row in result]

        return teams

    def _get_user_topics(self):
        """Retrieve all the topics that a user has acces to.
        """

        query = sql.select([models.TOPICS.c.id])
        if not self.is_super_admin() and not self.is_product_owner():
            query = query.select_from(
                sql.join(
                    models.TOPICS,
                    models.JOINS_TOPICS_TEAMS,
                    models.TOPICS.c.id == models.JOINS_TOPICS_TEAMS.c.topic_id
                )
            ).where(models.JOINS_TOPICS_TEAMS.c.team_id == self.team_id)
        elif self.is_product_owner():
            query = query.where(models.TOPICS.c.product_id == self.product_id)

        result = flask.g.db_conn.execute(query).fetchall()
        topics = []
        if result:
            topics = [row[models.TOPICS.c.id] for row in result]

        return topics

    def is_in_team(self, team_id):
        """Ensure the user is in the specified team."""

        return team_id in self.teams

    def is_super_admin(self):
        """Ensure the user has the role SUPER_ADMIN."""

        return self.role_id == v1_utils.get_role_id('SUPER_ADMIN')

    def is_product_owner(self):
        """Ensure the user has the role PRODUCT_OWNER."""

        return self.role_id == v1_utils.get_role_id('PRODUCT_OWNER')

    def is_team_product_owner(self, team_id):
        """Ensure the user has the role PRODUCT_OWNER and belongs
           to the team."""

        return self.role_id == v1_utils.get_role_id('PRODUCT_OWNER') and \
            self.is_in_team(team_id)

    def is_admin(self):
        """Ensure ther user has the role ADMIN."""

        return self.role_id == v1_utils.get_role_id('ADMIN')

    def is_team_admin(self, team_id):
        """Ensure the user has the role ADMIN and belongs to the team."""

        return self.role_id == v1_utils.get_role_id('ADMIN') and \
            self.is_in_team(team_id)

    def is_regular_user(self):
        """Ensure ther user has the role USER."""

        return self.role_id == v1_utils.get_role_id('USER')
