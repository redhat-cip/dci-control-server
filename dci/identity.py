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


class Identity:
    """Class that offers helper methods to simplify permission management
    """

    def __init__(self, user):
        for key in user.keys():
            setattr(self, key, user[key])

        self.teams = self._get_user_teams()

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

    def _get_role_id(self, label):
        """Return role id based on role label."""

        query = sql.select([models.ROLES]).where(
            models.ROLES.c.label == label
        )
        result = flask.g.db_conn.execute(query).fetchone()

        return result.id

    def is_in_team(self, team_id):
        """Ensure the user is in the specified team."""

        return team_id in self.teams

    def is_super_admin(self):
        """Ensure the user has the role SUPER_ADMIN."""

        return self.role_id == self._get_role_id('SUPER_ADMIN')

    def is_product_owner(self):
        """Ensure the user has the role PRODUCT_OWNER."""

        return self.role_id == self._get_role_id('PRODUCT_OWNER')

    def is_admin(self):
        """Ensure ther user has the role ADMIN."""

        return self.role_id == self._get_role_id('ADMIN')

    def is_regular_user(self):
        """Ensure ther user has the role USER."""

        return self.role_id == self._get_role_id('USER')
