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

from dci.server.db import models_core as models


def hash_password(password):
        return pwd_context.encrypt(password)


def check_auth(username, password):
    """Check the combination username/password that is valid on the
    database.
    """
    query_get_user = sqlalchemy.sql.select([models.USERS]).where(
        models.USERS.c.name == username)

    user = flask.g.db_conn.execute(query_get_user).fetchone()
    if user is None:
        return False
    user = dict(user)

    password_hash = hash_password(user.get('password'))
    return pwd_context.verify(password, password_hash)


def authenticate():
    """Sends a 401 response that enables basic auth."""

    auth_message = "Could not verify your access level for that URL. "\
                   "Please login with proper credentials."
    auth_message = json.dumps({'_status': 'Unauthorized',
                               'message': auth_message})

    headers = {'WWW-Authenticate': 'Basic realm="Login required"'}
    return flask.Response(auth_message, 401, headers=headers,
                          content_type='application/json')


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = flask.request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated
