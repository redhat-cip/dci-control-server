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
import sqlalchemy.sql
from passlib.apps import custom_app_context as pwd_context

from dci.db import models


class BaseMechanism(object):
    def __init__(self, request):
        self.request = request
        self.identity = None

    def is_valid(self):
        """Test if the user is a valid user."""
        pass


class BasicAuthMechanism(BaseMechanism):
    def is_valid(self):
        auth = self.request.authorization
        if not auth:
            return False
        user, is_authenticated = self.build_auth(auth.username, auth.password)
        if not is_authenticated:
            return False
        self.identity = user
        return True

    def build_auth(self, username, password):
        """Check the combination username/password that is valid on the
        database.
        """

        where_clause = sqlalchemy.sql.expression.and_(
            models.USERS.c.name == username,
            models.USERS.c.state == 'active',
            models.TEAMS.c.state == 'active'
        )
        t_j = sqlalchemy.join(
            models.USERS, models.TEAMS,
            models.USERS.c.team_id == models.TEAMS.c.id)
        query_get_user = (sqlalchemy.sql.select([
            models.USERS,
            models.TEAMS.c.name.label('team_name'),
            models.TEAMS.c.country.label('team_country'),
        ]).select_from(t_j).where(where_clause))

        user = flask.g.db_conn.execute(query_get_user).fetchone()
        if user is None:
            return None, False
        user = dict(user)

        return user, pwd_context.verify(password, user.get('password'))
