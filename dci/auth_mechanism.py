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
from datetime import datetime
import flask
import sqlalchemy.sql
from passlib.apps import custom_app_context as pwd_context

from dci.db import models
from dci.common import signature


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


class SignatureAuthMechanism(BaseMechanism):
    def is_valid(self):
        """Tries to authenticate a request using a signature as authentication
        mechanism.
        Returns True or False.
        Sets self.identity to the authenticated entity for later use.
        """
        # Get headers and extract information
        try:
            client_info = self.get_client_info()
        except ValueError:
            return False

        try:
            request_digest = self.request.headers.get('DCI-Auth-Signature')
        except ValueError:
            return False

        # Get remoteci
        remoteci = self.get_remoteci(client_info['id'])
        if remoteci is None:
            return False
        self.identity = dict(remoteci)
        # NOTE(fc): role assignment should be done in another place
        #           but this should do the job for now.
        self.identity['role'] = 'remoteci'

        # Actually verify signature
        return self.verify_remoteci_auth_signature(
            remoteci, client_info['timestamp'], request_digest)

    def get_client_info(self):
        """Extracts timestamp, client type and client id from a
        DCI-Client-Info header.
        Returns a hash with the three values.
        Throws an exception if the format is bad or if strptime fails."""
        bad_format_exception = \
            ValueError('DCI-Client-Info should match the following format: ' +
                       '"YYYY-MM-DD HH:MI:SSZ/<client_type>/<id>"')

        client_info = self.request.headers.get('DCI-Client-Info', '')
        client_info = client_info.split('/')
        if len(client_info) != 3 or not all(client_info):
            raise bad_format_exception

        dateformat = '%Y-%m-%d %H:%M:%SZ'
        return {
            'timestamp': datetime.strptime(client_info[0], dateformat),
            'type': client_info[1],
            'id': client_info[2],
        }

    @staticmethod
    def get_remoteci(ci_id):
        """Get the remoteci including its API secret
        """
        where_clause = sqlalchemy.sql.expression.and_(
            models.REMOTECIS.c.id == ci_id,
            models.REMOTECIS.c.active is True,
            models.REMOTECIS.c.state == 'active',
            models.TEAMS.c.state == 'active'
        )
        join_clause = sqlalchemy.join(
            models.REMOTECIS, models.TEAMS,
            models.REMOTECIS.c.team_id == models.TEAMS.c.id
        )
        query = (sqlalchemy
                 .select([
                     models.REMOTECIS,
                     models.TEAMS.c.name.label('team_name'),
                     models.TEAMS.c.country.label('team_country'),
                 ])
                 .select_from(join_clause)
                 .where(where_clause))
        remoteci = flask.g.db_conn.execute(query).fetchone()
        return remoteci

    def verify_remoteci_auth_signature(self, remoteci, timestamp,
                                       their_signature):
        """Extract the values from the request, and pass them to the signature
        verification method."""
        if remoteci.api_secret is None:
            return False

        url = self.request.path.encode('utf-8')
        query_string = self.request.query_string.encode('utf-8')

        return signature.is_signature_valid(
            their_signature,
            remoteci.api_secret, self.request.method,
            self.request.headers.get['Content-Type'], timestamp,
            url, query_string, self.request.data)
