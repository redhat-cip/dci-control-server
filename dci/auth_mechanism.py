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
from sqlalchemy import exc as sa_exc
from sqlalchemy import sql

from dci import auth
from dci.common import exceptions as dci_exc
from dciauth.request import AuthRequest
from dciauth.signature import Signature
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

    def identity_from_db(self, model_cls, model_constraint):
        partner_team = models.TEAMS.alias('partner_team')
        product_team = models.TEAMS.alias('product_team')

        query_get_identity = (
            sql.select(
                [
                    model_cls,
                    partner_team.c.name.label('team_name'),
                    models.PRODUCTS.c.id.label('product_id'),
                    models.ROLES.c.label.label('role_label'),
                    partner_team.c.state.label('partner_team_state'),
                ]
            ).select_from(
                model_cls.outerjoin(
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
                    sql.or_(
                        partner_team.c.state == 'active',
                        partner_team.c.state == None  # noqa
                    )
                )
            )
        )

        identity = flask.g.db_conn.execute(query_get_identity).fetchone()
        if identity is None:
            return None

        identity = dict(identity)
        teams = self._teams_from_db(identity['team_id'])

        return Identity(identity, teams)

    @staticmethod
    def get_team_and_children_teams(teams, team_id):
        return_teams = []
        for team in teams:
            if team['id'] == team_id:
                return_teams.append(team)
            if team['parent_id'] == team_id:
                return_teams += BaseMechanism.get_team_and_children_teams(
                    teams, team['id']
                )

        return return_teams

    def _teams_from_db(self, team_id):
        query = sql.select([models.TEAMS.c.id, models.TEAMS.c.parent_id])
        result = flask.g.db_conn.execute(query).fetchall()
        teams = [{
            'id': row[models.TEAMS.c.id],
            'parent_id': row[models.TEAMS.c.parent_id]
        } for row in result]

        return BaseMechanism.get_team_and_children_teams(teams, team_id)


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
        self.identity = user
        return True

    def get_user_and_check_auth(self, username, password):
        """Check the combination username/password that is valid on the
        database.
        """
        constraint = sql.or_(
            models.USERS.c.name == username,
            models.USERS.c.email == username
        )

        user = self.identity_from_db(models.USERS, constraint)
        if user is None:
            raise dci_exc.DCIException('User %s does not exists.' % username,
                                       status_code=401)

        return user, auth.check_passwords_equal(password, user.password)


class HmacMechanism(BaseMechanism):
    def authenticate(self):
        headers = self.request.headers
        auth_request = AuthRequest(
            method=self.request.method,
            endpoint=self.request.path,
            payload=self.request.get_json(silent=True),
            headers=headers,
            params=self.request.args.to_dict(flat=True)
        )
        hmac_signature = Signature(request=auth_request)
        self.identity = self.build_identity(auth_request.get_client_info())
        secret = getattr(self.identity, 'api_secret', '')
        if not hmac_signature.is_valid(secret):
            raise dci_exc.DCIException(
                'Authentication failed: signature invalid', status_code=401)
        if hmac_signature.is_expired():
            raise dci_exc.DCIException(
                'Authentication failed: signature expired', status_code=401)
        return True

    def build_identity(self, client_info):
        allowed_types_model = {
            'remoteci': models.REMOTECIS,
            'feeder': models.FEEDERS,
        }
        identity_model = allowed_types_model.get(client_info['client_type'])
        if identity_model is None:
            return None
        constraint = identity_model.c.id == client_info['client_id']
        return self.identity_from_db(identity_model, constraint)


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
        self.identity = self._get_user_from_sso_username(sso_username)
        if self.identity is None:
            self.identity = self._create_user_and_get(decoded_token)
            if self.identity is None:
                return False

    def _get_user_from_sso_username(self, sso_username):
        """Given the sso's username, get the associated user."""
        constraint = sql.or_(
            models.USERS.c.sso_username == sso_username,
            models.USERS.c.email == sso_username
        )

        identity = self.identity_from_db(models.USERS, constraint)
        return identity

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
