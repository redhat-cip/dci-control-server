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
from dci.identity import Identity

from jwt import exceptions as jwt_exc


class BaseMechanism(object):
    def __init__(self, request):
        self.request = request
        self.identity = None

    def authenticate(self):
        """Authenticate the user, if the user fail to authenticate then the
        method must raise an exception with proper error message."""
        pass

    def get_user_teams(self, user):
        """Retrieve all the teams that belongs to a user.

        SUPER_ADMIN own all teams.
        PRODUCT_OWNER own all teams attached to a product.
        ADMIN/USER own their own team
        """

        teams = []
        if not user['role_label'] == 'SUPER_ADMIN' and \
           not user['role_label'] == 'PRODUCT_OWNER':
            teams = [user['team_id']]
        else:
            query = sql.select([models.TEAMS.c.id])
            if user['role_label'] == 'PRODUCT_OWNER':
                query = query.where(
                    sql.or_(
                        models.TEAMS.c.parent_id == user['team_id'],
                        models.TEAMS.c.id == user['team_id']
                    )
                )

            result = flask.g.db_conn.execute(query).fetchall()
            teams = [row[models.TEAMS.c.id] for row in result]

        return teams


class BasicAuthMechanism(BaseMechanism):
    def authenticate(self):
        auth = self.request.authorization
        if not auth:
            raise dci_exc.DCIException('Authorization header missing',
                                       status_code=401)
        user, is_authenticated = \
            self.get_user_and_check_auth(auth.username, auth.password)
        if not is_authenticated:
            raise dci_exc.DCIException('Invalid user credentials',
                                       status_code=401)
        teams = self.get_user_teams(user)
        self.identity = Identity(user, teams)
        return True

    def get_user_and_check_auth(self, username, password):
        """Check the combination username/password that is valid on the
        database.
        """

        partner_team = models.TEAMS.alias('partner_team')
        product_team = models.TEAMS.alias('product_team')

        query_get_user = (
            sql.select(
                [
                    models.USERS,
                    partner_team.c.name.label('team_name'),
                    models.PRODUCTS.c.id.label('product_id'),
                    models.ROLES.c.label.label('role_label')
                ]
            ).select_from(
                sql.join(
                    models.USERS,
                    partner_team,
                    models.USERS.c.team_id == partner_team.c.id
                ).outerjoin(
                    product_team,
                    partner_team.c.parent_id == product_team.c.id
                ).outerjoin(
                    models.PRODUCTS,
                    models.PRODUCTS.c.team_id.in_([partner_team.c.id,
                                                   product_team.c.id])
                ).join(
                    models.ROLES,
                    models.USERS.c.role_id == models.ROLES.c.id
                )
            ).where(
                sql.and_(
                    sql.or_(
                        models.USERS.c.name == username,
                        models.USERS.c.email == username
                    ),
                    models.USERS.c.state == 'active',
                    partner_team.c.state == 'active'
                )
            )
        )

        user = flask.g.db_conn.execute(query_get_user).fetchone()
        if user is None:
            raise dci_exc.DCIException('User %s does not exists.' % username,
                                       status_code=401)
        user = dict(user)

        return user, auth.check_passwords_equal(password, user.get('password'))


class SignatureAuthMechanism(BaseMechanism):
    def authenticate(self):
        """Tries to authenticate a request using a signature as authentication
        mechanism.
        Sets self.identity to the authenticated entity for later use.
        """
        # Get headers and extract information

        client_info = self.get_client_info()
        their_signature = self.request.headers.get('DCI-Auth-Signature')

        remoteci = self.get_remoteci(client_info['id'])
        if remoteci is None:
            raise dci_exc.DCIException(
                'RemoteCI %s does not exist' % client_info['id'],
                status_code=401)
        dict_remoteci = dict(remoteci)
        # NOTE(fc): role assignment should be done in another place
        #           but this should do the job for now.
        dict_remoteci['role'] = 'remoteci'
        # TODO(spredzy): Remove once the REMOTECI role has been merged
        dict_remoteci['role_id'] = 'remoteci'
        dict_remoteci['role_label'] = 'REMOTECI'
        self.identity = Identity(dict_remoteci, [dict_remoteci['team_id']])

        if not self.verify_remoteci_auth_signature(
           remoteci, client_info['timestamp'], their_signature):
            raise dci_exc.DCIException('Invalid remotecI credentials.',
                                       status_code=401)

    def get_client_info(self):
        """Extracts timestamp, client type and client id from a
        DCI-Client-Info header.
        Returns a hash with the three values.
        Throws an exception if the format is bad or if strptime fails."""
        if 'DCI-Client-Info' not in self.request.headers:
            raise dci_exc.DCIException('Header DCI-Client-Info missing',
                                       status_code=401)

        client_info = self.request.headers.get('DCI-Client-Info')
        client_info = client_info.split('/')
        if len(client_info) != 3 or not all(client_info):
            raise dci_exc.DCIException(
                'DCI-Client-Info should match the following format: ' +
                '"YYYY-MM-DD HH:MI:SSZ/<client_type>/<id>"')

        dateformat = '%Y-%m-%d %H:%M:%SZ'
        try:
            timestamp = datetime.strptime(client_info[0], dateformat)
            return {
                'timestamp': timestamp,
                'type': client_info[1],
                'id': client_info[2],
            }
        except ValueError:
            raise dci_exc.DCIException('Bad date format in DCI-Client-Info',
                                       '401')

    @staticmethod
    def get_remoteci(ci_id):
        """Get the remoteci including its API secret
        """

        partner_team = models.TEAMS.alias('partner_team')
        product_team = models.TEAMS.alias('product_team')

        query_get_remoteci = (
            sql.select(
                [
                    models.REMOTECIS,
                    partner_team.c.name.label('team_name'),
                    models.PRODUCTS.c.id.label('product_id'),
                ]
            ).select_from(
                sql.join(
                    models.REMOTECIS,
                    partner_team,
                    models.REMOTECIS.c.team_id == partner_team.c.id
                ).outerjoin(
                    product_team,
                    partner_team.c.parent_id == product_team.c.id
                ).outerjoin(
                    models.PRODUCTS,
                    models.PRODUCTS.c.team_id.in_([partner_team.c.id,
                                                   product_team.c.id])
                )
            ).where(
                sql.and_(
                    models.REMOTECIS.c.id == ci_id,
                    models.REMOTECIS.c.state == 'active',
                    partner_team.c.state == 'active'
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
            raise dci_exc.DCIException('RemoteCI %s does not have an API'
                                       'secret set' % remoteci['id'],
                                       status_code=401)

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
    def authenticate(self):
        auth_header = self.request.headers.get('Authorization').split(' ')
        if len(auth_header) != 2:
            return False
        bearer, token = auth_header

        conf = dci_config.generate_conf()
        try:
            decoded_token = auth.decode_jwt(token,
                                            conf['SSO_PUBLIC_KEY'],
                                            conf['SSO_CLIENT_ID'])
        except jwt_exc.DecodeError:
            raise dci_exc.DCIException('Invalid JWT token.', status_code=401)
        except jwt_exc.ExpiredSignatureError:
            raise dci_exc.DCIException('JWT token expired, please refresh.',
                                       status_code=401)

        sso_username = decoded_token['username']
        user_from_sso_username = self._get_user_from_sso_username(sso_username)
        if user_from_sso_username is None:
            new_user = self._create_user_and_get(decoded_token)
            self.identity = Identity(new_user, [])
        else:
            user_teams = self.get_user_teams(user_from_sso_username)
            self.identity = Identity(user_from_sso_username, user_teams)

    def _get_user_from_sso_username(self, sso_username):
        """Given the sso's username, get the associated user."""

        partner_team = models.TEAMS.alias('partner_team')
        product_team = models.TEAMS.alias('product_team')

        query_get_user = (
            sql.select(
                [
                    models.USERS,
                    partner_team.c.name.label('team_name'),
                    models.PRODUCTS.c.id.label('product_id'),
                    models.ROLES.c.label.label('role_label')
                ]
            ).select_from(
                models.USERS.outerjoin(
                    partner_team,
                    models.USERS.c.team_id == partner_team.c.id
                ).outerjoin(
                    product_team,
                    partner_team.c.parent_id == product_team.c.id
                ).outerjoin(
                    models.PRODUCTS,
                    models.PRODUCTS.c.team_id.in_([partner_team.c.id,
                                                   product_team.c.id])
                ).join(
                    models.ROLES,
                    models.USERS.c.role_id == models.ROLES.c.id
                )
            ).where(
                sql.and_(
                    sql.or_(
                        models.USERS.c.sso_username == sso_username,
                        models.USERS.c.email == sso_username
                    ),
                    models.USERS.c.state == 'active'
                )
            )
        )

        user = flask.g.db_conn.execute(query_get_user).fetchone()

        return user and dict(user)

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
        except sa_exc.IntegrityError:
            raise dci_exc.DCICreationConflict(models.USERS.name, 'username')

        return self._get_user_from_sso_username(decoded_token.get('username'))
