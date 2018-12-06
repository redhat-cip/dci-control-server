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
from dci import dci_config
from dci.common import exceptions as dci_exc
from dciauth.request import AuthRequest
from dciauth.signature import Signature
from dci.db import models
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
        children_team = models.TEAMS.alias('children_team')
        product_team = models.TEAMS.alias('product_team')

        query_get_identity = (
            sql.select(
                [
                    model_cls,
                    children_team.c.name.label('team_name'),
                    models.PRODUCTS.c.id.label('product_id'),
                    models.ROLES.c.label.label('role_label'),
                    children_team.c.state.label('children_team_state'),
                ]
            ).select_from(
                model_cls.outerjoin(
                    children_team,
                    model_cls.c.team_id == children_team.c.id
                ).outerjoin(
                    product_team,
                    children_team.c.parent_id == product_team.c.id
                ).outerjoin(
                    models.PRODUCTS,
                    models.PRODUCTS.c.team_id.in_([children_team.c.id,
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
                        children_team.c.state == 'active',
                        children_team.c.state == None  # noqa
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

    def _teams_from_db(self, team_id):
        query = sql.select([models.TEAMS.c.id, models.TEAMS.c.parent_id])
        result = flask.g.db_conn.execute(query).fetchall()
        return [{
            'id': row[models.TEAMS.c.id],
            'parent_id': row[models.TEAMS.c.parent_id]
        } for row in result]


class BasicAuthMechanism(BaseMechanism):

    def authenticate(self):
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

        role_id = auth.get_role_id('USER')
        ro_group = dci_config.generate_conf().get('SSO_READ_ONLY_GROUP')
        realm_access = decoded_token['realm_access']
        if 'roles' in realm_access and ro_group in realm_access['roles']:
            role_id = auth.get_role_id('READ_ONLY_USER')

        user_info = self._get_user_info(decoded_token, role_id)
        try:
            self.identity = self._get_or_create_user(user_info)
        except sa_exc.IntegrityError:
            raise dci_exc.DCICreationConflict(models.USERS.name, 'username')
        return True

    @staticmethod
    def _get_user_info(token, user_role_id):
        return {
            'role_id': user_role_id,
            'name': token.get('username'),
            'fullname': token.get('username'),
            'sso_username': token.get('username'),
            'team_id': None,
            'email': token.get('email'),
            'timezone': 'UTC',
        }

    def _get_or_create_user(self, user_info):
        constraint = sql.or_(
            models.USERS.c.sso_username == user_info['sso_username'],
            models.USERS.c.email == user_info['sso_username'],
            models.USERS.c.email == user_info['email']
        )
        identity = self.identity_from_db(models.USERS, constraint)
        if identity is None:
            flask.g.db_conn.execute(models.USERS.insert().values(user_info))
            return self.identity_from_db(models.USERS, constraint)
        return identity
