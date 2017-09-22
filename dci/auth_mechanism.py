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
from sqlalchemy import exc as sa_exc
from sqlalchemy import sql

from dci import auth
from dci.common import exceptions as dci_exc
from dci.common import signature
from dci.db import models
from dci import dci_config


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
        user, is_authenticated = \
            self.get_user_and_check_auth(auth.username, auth.password)
        if not is_authenticated:
            return False
        self.identity = user
        return True

    def get_user_and_check_auth(self, username, password):
        """Check the combination username/password that is valid on the
        database.
        """

        query_get_user = (
            sql.select(
                [
                    models.USERS,
                    models.TEAMS.c.name.label('team_name'),
                ]
            ).select_from(
                sql.join(
                    models.USERS,
                    models.TEAMS,
                    models.USERS.c.team_id == models.TEAMS.c.id
                )
            ).where(
                sql.and_(
                    sql.or_(
                        models.USERS.c.name == username,
                        models.USERS.c.email == username
                    ),
                    models.USERS.c.state == 'active',
                    models.TEAMS.c.state == 'active'
                )
            )
        )

        user = flask.g.db_conn.execute(query_get_user).fetchone()
        if user is None:
            return None, False
        user = dict(user)

        return user, auth.check_passwords_equal(password, user.get('password'))


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
            their_signature = self.request.headers.get('DCI-Auth-Signature')
        except ValueError:
            return False

        remoteci = self.get_remoteci(client_info['id'])
        if remoteci is None:
            return False
        self.identity = dict(remoteci)
        # NOTE(fc): role assignment should be done in another place
        #           but this should do the job for now.
        self.identity['role'] = 'remoteci'

        return self.verify_remoteci_auth_signature(
            remoteci, client_info['timestamp'], their_signature)

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

        query_get_remoteci = (
            sql.select(
                [
                    models.REMOTECIS,
                    models.TEAMS.c.name.label('team_name'),
                ]
            ).select_from(
                sql.join(
                    models.REMOTECIS,
                    models.TEAMS,
                    models.REMOTECIS.c.team_id == models.TEAMS.c.id
                )
            ).where(
                sql.and_(
                    models.REMOTECIS.c.id == ci_id,
                    models.REMOTECIS.c.state == 'active',
                    models.TEAMS.c.state == 'active'
                )
            )
        )

        remoteci = flask.g.db_conn.execute(query_get_remoteci).fetchone()
        return remoteci

    def verify_remoteci_auth_signature(self, remoteci, timestamp,
                                       their_signature):
        """Extract the values from the request, and pass them to the signature
        verification method."""
        if remoteci.api_secret is None:
            return False

        return signature.is_valid(
            their_signature=their_signature.encode('utf-8'),
            secret=remoteci.api_secret.encode('utf-8'),
            http_verb=self.request.method.upper().encode('utf-8'),
            content_type=(self.request.headers.get('Content-Type')
                          .encode('utf-8')),
            timestamp=timestamp,
            url=self.request.path.encode('utf-8'),
            query_string=self.request.query_string,
            payload=self.request.data)


class OpenIDCAuth(BaseMechanism):
    def is_valid(self):
        auth_header = self.request.headers.get('Authorization').split(' ')
        if len(auth_header) != 2:
            return False
        bearer, token = auth_header

        if bearer != 'Bearer':
            return False

        conf = dci_config.generate_conf()
        try:
            decoded_token = auth.decode_jwt(token,
                                            conf['SSO_PUBLIC_KEY'],
                                            'dci-cs')
        except Exception:
            return False

        sso_username = decoded_token['username']
        self.identity = self._get_user_from_sso_username(sso_username)

        if self.identity is None:
            self.identity = self._create_user_and_get(decoded_token)

        return True

    def _get_user_from_sso_username(self, sso_username):
        """Given the sso's username, get the associated user."""

        query_get_user = (
            sql.select(
                [models.USERS]
            ).where(
                models.USERS.c.sso_username == sso_username
            )
        )

        user = flask.g.db_conn.execute(query_get_user).fetchone()
        if user is None:
            return None
        return dict(user)

    def _create_user_and_get(self, decoded_token):
        """Create the user according to the token, this function assume that
        the token has been verified."""

        user_values = {
            'role_id': auth.get_role_id('USER'),
            'name': decoded_token.get('username'),
            'fullname': decoded_token.get('username'),
            'sso_username': decoded_token.get('username'),
            'team_id': None,
            'email': decoded_token.get('email'),
            'timezone': 'UTC',
        }

        query = models.USERS.insert().values(user_values)

        try:
            flask.g.db_conn.execute(query)
        except sa_exc.IntegrityError as e:
            print(str(e))
            raise dci_exc.DCICreationConflict(models.USERS.name, 'username')

        return self._get_user_from_sso_username(decoded_token.get('username'))
