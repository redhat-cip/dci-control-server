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

# ACCESS RIGHTS
# A user of a normal team with 'user' role.
USER = 0
# An admin of a normal team with 'admin' role.
ADMIN_USER = 1
# A user of the 'admin' team with 'user' role.
ADMIN = 2
# The super admin, belongs to the 'admin' team with the 'admin' role.
SUPER_ADMIN = 3

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

    if user['team_id'] == dci_config.TEAM_ADMIN_ID:
        user_access = ADMIN
        if user['role'] == 'admin':
            user_access = SUPER_ADMIN
    elif user['role'] == 'admin':
        user_access = ADMIN_USER
    else:
        user_access = USER

    user['user_access'] = user_access

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


def check_admin_or_same_team(user, team_id):
    if user['user_access'] < ADMIN and user['team_id'] != team_id:
        raise UNAUTHORIZED


def check_admin_or_admin_user_team(user, team_id):
    if (user['user_access'] < ADMIN and
            (user['team_id'] != team_id or user['role'] != 'admin')):
        raise UNAUTHORIZED


def is_admin(user_info):
    return user_info['user_access'] > ADMIN_USER


def requires_auth(level=USER):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = flask.request.authorization
            if not auth:
                return reject()
            user, is_authenticated = build_auth(auth.username, auth.password)
            if not is_authenticated:
                return reject()

            if user['user_access'] < level:
                raise UNAUTHORIZED

            return f(user, *args, **kwargs)

        return decorated
    return wrapper
