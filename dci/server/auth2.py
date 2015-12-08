# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Red Hat, Inc
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
from functools import wraps
import json
from passlib.apps import custom_app_context as pwd_context
import sqlalchemy.sql

from dci.server.common import exceptions as exc
from dci.server.db import models_core as models
from dci.server import dci_config


UNAUTHORIZED = exc.DCIException('Operation not authorized.', status_code=401)


def hash_password(password):
        return pwd_context.encrypt(password)


def build_auth(username, password):
    """Check the combination username/password that is valid on the
    database.
    """
    query_get_user = (sqlalchemy.sql
                      .select([models.USERS])
                      .where(models.USERS.c.name == username))

    user = flask.g.db_conn.execute(query_get_user).fetchone()
    if user is None:
        return None, False
    user = dict(user)

    return user, pwd_context.verify(password, user.get('password'))


def reject():
    """Sends a 401 reject response that enables basic auth."""

    auth_message = ('Could not verify your access level for that URL.'
                    'Please login with proper credentials.')
    auth_message = json.dumps({'_status': 'Unauthorized',
                               'message': auth_message})

    headers = {'WWW-Authenticate': 'Basic realm="Login required"'}
    return flask.Response(auth_message, 401, headers=headers,
                          content_type='application/json')


def is_admin(user):
    return user['team_id'] == dci_config.TEAM_ADMIN_ID


def is_super_admin(user):
    return is_admin(user) and user['role'] == 'admin'


def is_admin_or_in_same_team(user, team_id):
    if not is_admin(user) and user['team_id'] != team_id:
        raise UNAUTHORIZED


def is_admin_or_admin_user_in_same_team(user, team_id):
    if (not is_admin(user) and
            (user['team_id'] != team_id or user['role'] != 'admin')):
        raise UNAUTHORIZED


def requires_auth():
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = flask.request.authorization
            if not auth:
                return reject()
            user, is_authenticated = build_auth(auth.username, auth.password)
            if not is_authenticated:
                return reject()
            return f(user, *args, **kwargs)
        return decorated
    return wrapper
