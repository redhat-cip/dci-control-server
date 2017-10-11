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
from sqlalchemy import sql

from dci.db import models


class Identity:
    """Class that offers helper methods to simplify permission management
    """

    def __init__(self, user):
        for key in user.keys():
            setattr(self, key, user[key])

        self._teams_from_db()

    @classmethod
    def from_db(cls, model_cls, model_constraint):
        partner_team = models.TEAMS.alias('partner_team')
        product_team = models.TEAMS.alias('product_team')

        query_get_identity = (
            sql.select(
                [
                    model_cls,
                    partner_team.c.name.label('team_name'),
                    models.PRODUCTS.c.id.label('product_id'),
                    models.ROLES.c.label.label('role_label')
                ]
            ).select_from(
                sql.join(
                    model_cls,
                    partner_team,
                    model_cls.c.team_id == partner_team.c.id
                ).outerjoin(
                    product_team,
                    partner_team.c.parent_id == product_team.c.id
                ).outerjoin(
                    models.PRODUCTS,
                    models.PRODUCTS.c.team_id.in_([partner_team.c.id,
                                                   product_team.c.id])
                ).join(
                    models.ROLES,
                    model_cls.c.role_id == models.ROLES.c.id
                )
            ).where(
                sql.and_(
                    model_constraint,
                    model_cls.c.state == 'active',
                    partner_team.c.state == 'active'
                )
            )
        )

        identity = flask.g.db_conn.execute(query_get_identity).fetchone()
        if identity is None:
            return None

        identity = dict(identity)
        return cls(identity)

    def _teams_from_db(self):
        """Retrieve all the teams that belongs to a user.

        SUPER_ADMIN own all teams.
        PRODUCT_OWNER own all teams attached to a product.
        ADMIN/USER own their own team
        """

        if not self.role_label == 'SUPER_ADMIN' and \
           not self.role_label == 'PRODUCT_OWNER':
            self.teams = [self.team_id]
        else:
            query = sql.select([models.TEAMS.c.id])
            if self.role_label == 'PRODUCT_OWNER':
                query = query.where(
                    sql.or_(
                        models.TEAMS.c.parent_id == self.team_id,
                        models.TEAMS.c.id == self.team_id
                    )
                )

            result = flask.g.db_conn.execute(query).fetchall()
            self.teams = [row[models.TEAMS.c.id] for row in result]

    # TODO(spredzy): In order to avoid a huge refactor patch, the __getitem__
    # function is overloaded so it behaves like a dict and the code in place
    # can work transparently
    def __getitem__(self, key):
        return getattr(self, key)

    def is_in_team(self, team_id):
        """Ensure the user is in the specified team."""

        return team_id in self.teams

    def is_super_admin(self):
        """Ensure the user has the role SUPER_ADMIN."""

        return self.role_label == 'SUPER_ADMIN'

    def is_product_owner(self):
        """Ensure the user has the role PRODUCT_OWNER."""

        return self.role_label == 'PRODUCT_OWNER'

    def is_team_product_owner(self, team_id):
        """Ensure the user has the role PRODUCT_OWNER and belongs
           to the team."""

        return self.role_label == 'PRODUCT_OWNER' and \
            self.is_in_team(team_id)

    def is_admin(self):
        """Ensure the user has the role ADMIN."""

        return self.role_label == 'ADMIN'

    def is_team_admin(self, team_id):
        """Ensure the user has the role ADMIN and belongs to the team."""

        return self.role_label == 'ADMIN' and self.is_in_team(team_id)

    def is_regular_user(self):
        """Ensure the user has the role USER."""

        return self.role_label == 'USER'

    def is_remoteci(self):
        """Ensure ther resource has the role REMOTECI."""

        return self.role_label == 'REMOTECI'
