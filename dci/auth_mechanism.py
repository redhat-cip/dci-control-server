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
import uuid
from sqlalchemy import exc as sa_exc
from sqlalchemy import sql
from sqlalchemy import orm

from dci.api.v1 import base, sso
from dci.auth import check_passwords_equal, decode_jwt
from dci import dci_config
from dci.common import exceptions as dci_exc
from dciauth.v2.headers import parse_headers
from dciauth.v2.signature import is_valid
from dci.db import models2
from dci.identity import Identity

import logging
from jwt import exceptions as jwt_exc

logger = logging.getLogger(__name__)


class BaseMechanism(object):
    def __init__(self, request):
        self.request = request
        self.identity = None

    def authenticate(self):
        """Authenticate the user, if the user fail to authenticate then the
        method must raise an exception with proper error message."""
        pass

    def get_user(self, model_constraint):
        try:
            return (
                flask.g.session.query(models2.User)
                .filter(models2.User.state == "active")
                .options(orm.selectinload("team"))
                .filter(model_constraint)
                .one()
            )
        except orm.exc.NoResultFound:
            return None

    def get_scoped_team_id(self):
        scoped_team_id = self.request.headers.get("X-Dci-Team-Id")
        if scoped_team_id:
            return uuid.UUID(scoped_team_id)
        return None

    def identity_from_user(self, user):
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
        scoped_team_id = self.get_scoped_team_id()
        for user_team in user.team:
            team_id = user_team.id
            if team_id == flask.g.team_admin_id:
                is_super_admin = True
            if team_id == flask.g.team_redhat_id:
                is_read_only_user = True
            if team_id == flask.g.team_epm_id:
                is_epm_user = True
            if scoped_team_id and scoped_team_id != team_id:
                continue
            # TODO (gvincent): use user_team.serialize()
            user_teams[team_id] = {
                "id": team_id,
                "name": user_team.name,
                "has_pre_release_access": user_team.has_pre_release_access,
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

        username = auth.username
        user = self.get_user(models2.User.name == username)
        if user is None:
            user = self.get_user(models2.User.email == username)
            if user is None:
                raise dci_exc.DCIException(
                    "User %s does not exists." % username, status_code=401
                )
        is_authenticated = check_passwords_equal(auth.password, user.password)
        if not is_authenticated:
            raise dci_exc.DCIException("Invalid user credentials", status_code=401)
        self.identity = self.identity_from_user(user)
        return True


class HmacMechanism(BaseMechanism):
    def authenticate(self):
        headers = parse_headers(self.request.headers)
        if not headers:
            raise dci_exc.DCIException(
                "HmacMechanism failed: bad or incomplete headers.", status_code=400
            )
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
            raise dci_exc.DCIException("HmacMechanism failed: %s" % error_message)
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
            identity_model, client_info["client_id"], options=[orm.selectinload("team")]
        )
        return Identity(
            {
                "id": str(identity.id),
                "teams": {
                    identity.team.id: {
                        "team_name": identity.team.name,
                        "state": identity.team.state,
                        "has_pre_release_access": identity.team.has_pre_release_access,
                    }
                },
                "api_secret": str(identity.api_secret),
                "is_remoteci": client_type == "remoteci",
                "is_feeder": client_type == "feeder",
                "is_read_only_user": identity.team.id == flask.g.team_redhat_id,
            }
        )


class OpenIDCAuth(BaseMechanism):
    def authenticate(self):
        auth_header = self.request.headers.get("Authorization").split(" ")
        if len(auth_header) != 2:
            return False
        _, token = auth_header
        conf = dci_config.CONFIG

        def __get_and_set_sso_public_key():
            public_key = sso.get_public_key_from_token(token)
            if public_key and public_key != conf.get("SSO_PUBLIC_KEY"):
                logging.info("sso public key has been updated")
                logging.debug(public_key)
                conf["SSO_PUBLIC_KEY"] = public_key

        if not conf.get("SSO_PUBLIC_KEY"):
            __get_and_set_sso_public_key()

        try:
            decoded_token = decode_jwt(
                token, conf["SSO_PUBLIC_KEY"], conf["SSO_AUDIENCES"]
            )
        except (jwt_exc.DecodeError, TypeError, ValueError) as e:
            logging.debug(
                "JWT token decode error: %s, will refresh sso public key and retry decode"
                % str(e)
            )
            try:
                __get_and_set_sso_public_key()
                decoded_token = decode_jwt(
                    token, conf["SSO_PUBLIC_KEY"], conf["SSO_AUDIENCES"]
                )
            except (jwt_exc.DecodeError, TypeError, ValueError) as e2:
                raise dci_exc.DCIException(
                    "JWT token decode error: %s" % str(e2), status_code=401
                )
        except jwt_exc.ExpiredSignatureError:
            raise dci_exc.DCIException(
                "JWT token expired, please refresh.", status_code=401
            )

        team_id = None
        read_only_group = conf["SSO_READ_ONLY_GROUP"]
        if self._is_read_only_user(decoded_token, read_only_group):
            team_id = flask.g.team_redhat_id

        user_info = self._get_user_info(decoded_token)
        try:
            self.identity = self._get_or_update_or_create_user(user_info, team_id)
        except sa_exc.IntegrityError:
            raise dci_exc.DCICreationConflict("users", "username")
        return True

    @staticmethod
    def _is_read_only_user(token, read_only_group):
        # todo(gvincent): implement the solution with idp and verified email
        try:
            realm_access = token["realm_access"]
            return "roles" in realm_access and read_only_group in realm_access["roles"]
        except:
            return False

    @staticmethod
    def _get_user_info(token):
        username = token.get("preferred_username", token.get("username"))
        sso_sub = None if token.get("scope", "openid") == "openid" else token.get("sub")
        return {
            "name": username,
            "fullname": token.get("name", username),
            "sso_username": username,
            "sso_sub": sso_sub,
            "email": token.get("email"),
            "timezone": "UTC",
        }

    def _get_or_update_or_create_user(self, user_info, team_id=None):
        sso_username = user_info["sso_username"]
        if not sso_username:
            raise Exception(
                "Red Hat login is required. Please contact a DCI administrator."
            )
        user = self._get_user_with_email_and_red_hat_login(user_info)
        if user:
            return self.identity_from_user(user)

        user = self._get_user_with_only_red_hat_login(user_info)
        if user:
            user_updated = self._update_user(user, user_info)
            return self.identity_from_user(user_updated)

        user_created = self._create_user(user_info, team_id)
        return self.identity_from_user(user_created)

    def _get_user_with_email_and_red_hat_login(self, user_info):
        sso_username = user_info["sso_username"]
        email = user_info["email"]
        existing_user_constraint = sql.and_(
            models2.User.sso_username == sso_username,
            models2.User.email == email,
        )
        return self.get_user(existing_user_constraint)

    def _get_user_with_only_red_hat_login(self, user_info):
        return self.get_user(models2.User.sso_username == user_info["sso_username"])

    def _create_user(self, user_info, team_id):
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
        return self._get_user_with_email_and_red_hat_login(user_info)

    def _update_user(self, user, user_info):
        base.update_resource_orm(user, {"email": user_info["email"]})
        return self._get_user_with_email_and_red_hat_login(user_info)
