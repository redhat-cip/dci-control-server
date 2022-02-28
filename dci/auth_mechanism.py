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
from sqlalchemy import orm

from dci.api.v1 import base, sso
from dci import auth
from dci import dci_config
from dci.common import exceptions as dci_exc
from dciauth.request import AuthRequest
from dciauth.signature import Signature
from dciauth.v2.headers import parse_headers
from dciauth.v2.signature import is_valid
from dci.db import models2
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

    def identity_from_db(self, model_constraint):
        try:
            user = (
                flask.g.session.query(models2.User)
                .filter(models2.User.state == "active")
                .options(orm.joinedload("team"))
                .filter(model_constraint)
                .one()
            )
        except orm.exc.NoResultFound:
            return None

        user_info = {
            # UUID to str
            "id": str(user.id),
            "password": user.password,
            "name": user.name,
            "fullname": user.fullname,
            "timezone": user.timezone,
            "email": user.email,
            "sso_username": user.sso_username,
            "etag": user.etag,
            "is_user": True,
        }

        is_super_admin = False
        is_read_only_user = False
        is_epm_user = False
        user_teams = {}
        for user_team in user.team:
            if user_team.id == flask.g.team_admin_id:
                is_super_admin = True
            if user_team.id == flask.g.team_redhat_id:
                is_read_only_user = True
            if user_team.id == flask.g.team_epm_id:
                is_epm_user = True
            # todo gvincent: use user_team.serialize()
            user_teams[user_team.id] = {
                "id": user_team.id,
                "name": user_team.name,
            }

        user_info["teams"] = user_teams
        user_info["is_super_admin"] = is_super_admin
        user_info["is_read_only_user"] = is_read_only_user
        user_info["is_epm_user"] = is_epm_user

        return Identity(user_info)

    def check_team_is_active(self, team_id):
        if self.identity.teams[team_id]["state"] != "active":
            name = self.identity.teams[team_id]["team_name"]
            raise dci_exc.DCIException("team %s not active" % name, status_code=412)


class BasicAuthMechanism(BaseMechanism):
    def authenticate(self):
        auth = self.request.authorization
        if not auth:
            raise dci_exc.DCIException("Authorization header missing", status_code=401)
        user, is_authenticated = self.get_user_and_check_auth(
            auth.username, auth.password
        )
        if not is_authenticated:
            raise dci_exc.DCIException("Invalid user credentials", status_code=401)
        self.identity = user
        return True

    def get_user_and_check_auth(self, username, password):
        """Check the combination username/password that is valid on the
        database.
        """
        constraint = sql.or_(
            models2.User.name == username, models2.User.email == username
        )
        user = self.identity_from_db(constraint)
        if user is None:
            raise dci_exc.DCIException(
                "User %s does not exists." % username, status_code=401
            )

        return user, auth.check_passwords_equal(password, user.password)


class HmacMechanism(BaseMechanism):
    def authenticate(self):
        headers = self.request.headers
        auth_request = AuthRequest(
            method=self.request.method,
            endpoint=self.request.path,
            payload=self.request.get_json(silent=True),
            headers=headers,
            params=self.request.args.to_dict(flat=True),
        )
        hmac_signature = Signature(request=auth_request)
        self.identity = self.build_identity(auth_request.get_client_info())
        if self.identity is None:
            raise dci_exc.DCIException("identity does not exists.", status_code=401)
        secret = self.identity.api_secret
        if not hmac_signature.is_valid(secret):
            raise dci_exc.DCIException(
                "HmacMechanism failed: signature invalid",
                status_code=401,
            )
        if hmac_signature.is_expired():
            raise dci_exc.DCIException(
                "HmacMechanism failed: signature expired",
                status_code=401,
            )
        if len(self.identity.teams_ids) > 0:
            self.check_team_is_active(self.identity.teams_ids[0])
        return True

    def build_identity(self, client_info):
        allowed_types_model = {
            "remoteci": models2.Remoteci,
            "feeder": models2.Feeder,
        }
        client_type = client_info["client_type"]
        identity_model = allowed_types_model.get(client_type)
        if identity_model is None:
            return None
        identity = base.get_resource_orm(
            identity_model, client_info["client_id"], options=[orm.joinedload("team")]
        )
        return Identity(
            {
                "id": str(identity.id),
                "teams": {
                    identity.team.id: {
                        "team_name": identity.team.name,
                        "state": identity.team.state,
                    }
                },
                "api_secret": str(identity.api_secret),
                "is_remoteci": client_type == "remoteci",
                "is_feeder": client_type == "feeder",
            }
        )


class Hmac2Mechanism(HmacMechanism):
    def authenticate(self):
        headers = parse_headers(self.request.headers)
        self.identity = self.build_identity(headers)
        if self.identity is None:
            raise dci_exc.DCIException("identity does not exists.", status_code=401)
        valid, error_message = is_valid(
            {
                "method": self.request.method,
                "endpoint": self.request.path,
                "data": self.request.data,
                "params": self.request.args.to_dict(flat=True),
            },
            {"secret_key": self.identity.api_secret},
            headers,
        )
        if not valid:
            raise dci_exc.DCIException("Hmac2Mechanism failed: %s" % error_message)
        if len(self.identity.teams_ids) > 0:
            self.check_team_is_active(self.identity.teams_ids[0])
        return True


class OpenIDCAuth(BaseMechanism):
    def authenticate(self):
        auth_header = self.request.headers.get("Authorization").split(" ")
        if len(auth_header) != 2:
            return False
        bearer, token = auth_header

        conf = dci_config.CONFIG
        try:
            decoded_token = auth.decode_jwt(
                token, conf["SSO_PUBLIC_KEY"], conf["SSO_CLIENT_ID"]
            )
        except (jwt_exc.DecodeError, ValueError):
            decoded_token = sso.decode_token_with_latest_public_key(token)
        except jwt_exc.ExpiredSignatureError:
            raise dci_exc.DCIException(
                "JWT token expired, please refresh.", status_code=401
            )

        team_id = None
        ro_group = conf["SSO_READ_ONLY_GROUP"]
        realm_access = decoded_token["realm_access"]
        if "roles" in realm_access and ro_group in realm_access["roles"]:
            team_id = flask.g.team_redhat_id

        user_info = self._get_user_info(decoded_token)
        try:
            self.identity = self._get_or_create_user(user_info, team_id)
        except sa_exc.IntegrityError:
            raise dci_exc.DCICreationConflict("users", "username")
        return True

    @staticmethod
    def _get_user_info(token):
        return {
            "name": token.get("username"),
            "fullname": token.get("username"),
            "sso_username": token.get("username"),
            "email": token.get("email"),
            "timezone": "UTC",
        }

    def _get_or_create_user(self, user_info, team_id=None):
        constraint = sql.or_(
            models2.User.sso_username == user_info["sso_username"],
            models2.User.email == user_info["sso_username"],
            models2.User.email == user_info["email"],
        )
        identity = self.identity_from_db(constraint)
        if identity is None:
            try:
                user = models2.User(**user_info)
                flask.g.session.add(user)
                flask.g.session.commit()
                if team_id is not None:
                    team = base.get_resource_orm(models2.Team, team_id)
                    team.users.append(user)
                    flask.g.session.add(team)
                    flask.g.session.commit()
            except Exception:
                flask.g.session.rollback()
                raise dci_exc.DCIException(
                    message="Cannot create user in Open ID Connect auth mechanism"
                )
            identity = self.identity_from_db(constraint)
            return identity
        return identity
