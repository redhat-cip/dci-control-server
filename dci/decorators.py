# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Red Hat, Inc
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

import json
from functools import wraps

import flask
from sqlalchemy import sql

from dci import auth_mechanism
from dci.common import exceptions as dci_exc
from dci.policies import ROLES
from dci.db import models


def reject():
    """Sends a 401 reject response that enables basic auth."""

    auth_message = (
        "Could not verify your access level for that URL."
        "Please login with proper credentials."
    )
    auth_message = json.dumps({"_status": "Unauthorized", "message": auth_message})

    headers = {"WWW-Authenticate": 'Basic realm="Login required"'}
    return flask.Response(
        auth_message, 401, headers=headers, content_type="application/json"
    )


def _get_auth_class_from_headers(headers):
    if "Authorization" not in headers:
        raise dci_exc.DCIException("Authorization header missing", status_code=401)

    auth_type = headers.get("Authorization").split(" ")[0]
    if auth_type == "Bearer":
        return auth_mechanism.OpenIDCAuth
    elif auth_type == "DCI-HMAC-SHA256":
        return auth_mechanism.HmacMechanism
    elif auth_type == "Basic":
        return auth_mechanism.BasicAuthMechanism

    raise dci_exc.DCIException(
        "Authorization scheme %s unknown" % auth_type, status_code=401
    )


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_class = _get_auth_class_from_headers(flask.request.headers)
        auth_scheme = auth_class(flask.request)
        auth_scheme.authenticate()
        return f(auth_scheme.identity, *args, **kwargs)

    return decorated


def check_roles(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        identity = args[0]
        if identity.role_label in ROLES[f.__name__]:
            return f(*args, **kwargs)
        raise dci_exc.Unauthorized()

    return decorated


def check_identity_is_in_user_id_team(get_user_id):
    def decorator(f):
        @wraps(f)
        def wrap(*args, **kwargs):
            identity = args[0]
            user_id = get_user_id(*args, **kwargs)
            query = sql.select([models.USERS]).where(models.USERS.c.id == user_id)
            r = flask.g.db_conn.execute(query).fetchone()
            if not r:
                raise dci_exc.DCINotFound
            team_id = dict(r)["team_id"]
            if identity.is_super_admin() or (
                team_id and team_id == identity.team["id"]
            ):
                return f(*args, **kwargs)
            raise dci_exc.Unauthorized

        return wrap

    return decorator
