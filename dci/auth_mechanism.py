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

        q_get_user_teams = (
            sql.select(
                [
                    model_cls,
                    models.TEAMS,
                    models.JOIN_USERS_TEAMS
                ],
                use_labels=True
            ).select_from(
                model_cls.join(
                    models.JOIN_USERS_TEAMS,
                    models.JOIN_USERS_TEAMS.c.user_id == model_cls.c.id
                ).outerjoin(
                    models.TEAMS,
                    (models.JOIN_USERS_TEAMS.c.team_id ==
                     models.TEAMS.c.id)
                )
            ).where(
                sql.and_(
                    model_constraint,
                    model_cls.c.state == 'active',
                )
            )
        )

        _user_teams = flask.g.db_conn.execute(q_get_user_teams).fetchall()
        if not _user_teams:
            return None

        user_info = {
            # UUID to str
            'id': str(_user_teams[0][model_cls.c.id]),
            'password': _user_teams[0][model_cls.c.password],
            'name': _user_teams[0][model_cls.c.name],
            'fullname': _user_teams[0][model_cls.c.fullname],
            'timezone': _user_teams[0][model_cls.c.timezone],
            'email': _user_teams[0][model_cls.c.email],
            'sso_username': _user_teams[0][model_cls.c.sso_username],
            'etag': _user_teams[0][model_cls.c.etag],
            'is_user': True
        }

        is_super_admin = False
        is_read_only_user = False
        is_epm_user = False
        user_teams = {}
        for user_team in _user_teams:
            if user_team[models.TEAMS.c.id] == flask.g.team_admin_id:
                is_super_admin = True
            if user_team[models.TEAMS.c.id] == flask.g.team_redhat_id:
                is_read_only_user = True
            if user_team[models.TEAMS.c.id] == flask.g.team_epm_id:
                is_epm_user = True
            user_teams[user_team[models.TEAMS.c.id]] = {
                'id': user_team[models.TEAMS.c.id],
                'name': user_team[models.TEAMS.c.name]}

        user_info['teams'] = user_teams
        user_info['is_super_admin'] = is_super_admin
        user_info['is_read_only_user'] = is_read_only_user
        user_info['is_epm_user'] = is_epm_user

        return Identity(user_info)


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
        if self.identity is None:
            raise dci_exc.DCIException('identity does not exists.',
                                       status_code=401)
        secret = self.identity.api_secret
        if not hmac_signature.is_valid(secret):
            raise dci_exc.DCIException(
                'Authentication failed: signature invalid', status_code=401)
        if hmac_signature.is_expired():
            raise dci_exc.DCIException(
                'Authentication failed: signature expired', status_code=401)
        return True

    def identity_from_db(self, model_cls, model_constraint):
        q_get_identity = (
            sql.select(
                [
                    model_cls,
                    models.TEAMS
                ],
                use_labels=True
            ).select_from(
                model_cls.join(
                    models.TEAMS,
                    models.TEAMS.c.id == model_cls.c.team_id
                )
            ).where(
                sql.and_(
                    model_constraint,
                    model_cls.c.state != 'archived',
                )
            )
        )

        _identity_info = flask.g.db_conn.execute(q_get_identity).fetchone()
        if not _identity_info:
            return None

        # feeders and remotecis belongs to only one team
        user_teams = {
            _identity_info[models.TEAMS.c.id]: {
                'team_name': _identity_info[models.TEAMS.c.name]
            }
        }

        is_remoteci = False
        if model_cls is models.REMOTECIS:
            is_remoteci = True
        is_feeder = False
        if model_cls is models.FEEDERS:
            is_feeder = True

        user_info = {
            # UUID to str
            'id': str(_identity_info[model_cls.c.id]),
            'teams': user_teams,
            'api_secret': str(_identity_info[model_cls.c.api_secret]),
            'is_remoteci': is_remoteci,
            'is_feeder': is_feeder
        }
        return Identity(user_info)

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

        team_id = None
        ro_group = dci_config.generate_conf().get('SSO_READ_ONLY_GROUP')
        realm_access = decoded_token['realm_access']
        if 'roles' in realm_access and ro_group in realm_access['roles']:
            team_id = flask.g.team_redhat_id

        user_info = self._get_user_info(decoded_token, team_id)
        try:
            self.identity = self._get_or_create_user(user_info)
        except sa_exc.IntegrityError:
            raise dci_exc.DCICreationConflict(models.USERS.name, 'username')
        return True

    @staticmethod
    def _get_user_info(token, team_id):
        return {
            'name': token.get('username'),
            'fullname': token.get('username'),
            'sso_username': token.get('username'),
            'team_id': team_id,
            'email': token.get('email'),
            'timezone': 'UTC',
        }

    def _get_or_create_user(self, user_info):
        constraint = sql.or_(
            models.USERS.c.sso_username == user_info['sso_username'],
            models.USERS.c.email == user_info['sso_username'],
            models.USERS.c.email == user_info['email']
        )
        identity = self.identity_from_db(models.USERS,
                                         constraint)
        if identity is None:
            u_id = flask.g.db_conn.execute(models.USERS.insert().values(user_info)).inserted_primary_key[0]  # noqa
            flask.g.db_conn.execute(
                models.JOIN_USERS_TEAMS.insert().values(
                    user_id=u_id,
                    team_id=user_info['team_id']
                )
            )
            identity = self.identity_from_db(models.USERS,
                                             constraint)
            return identity
        return identity
