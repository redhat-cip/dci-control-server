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
from passlib.apps import custom_app_context as pwd_context

from dci.auth_mechanism import BasicAuthMechanism, SignatureAuthMechanism
from dci.db import models
from dci.common import exceptions as exc
from sqlalchemy import sql

UNAUTHORIZED = exc.DCIException('Operation not authorized.', status_code=401)


def hash_password(password):
    return pwd_context.encrypt(password)


def reject():
    """Sends a 401 reject response that enables basic auth."""

    auth_message = ('Could not verify your access level for that URL.'
                    'Please login with proper credentials.')
    auth_message = json.dumps({'_status': 'Unauthorized',
                               'message': auth_message})

    headers = {'WWW-Authenticate': 'Basic realm="Login required"'}
    return flask.Response(auth_message, 401, headers=headers,
                          content_type='application/json')


# This method should be deleted once permissions mechanism is
# in place. Meanwhile, for the migration to be seamless, we
# need to have this method around
def get_role_id(label):
    """Return role id based on role label."""

    query = sql.select([models.ROLES]).where(
        models.ROLES.c.label == label
    )
    result = flask.g.db_conn.execute(query).fetchone()
    return result.id


def is_admin(user, super=False):
    if super and user['role'] != 'admin':
        return False
    return user['team_name'] == 'admin'


def is_admin_user(user, team_id):
    return str(user['team_id']) == str(team_id) and user['role'] == 'admin'


def is_in_team(user, team_id):
    return str(user['team_id']) == str(team_id)


def check_export_control(user, component):
    if not is_admin(user):
        if not component['export_control']:
            raise UNAUTHORIZED


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        for mechanism in [BasicAuthMechanism(flask.request),
                          SignatureAuthMechanism(flask.request)]:
            if mechanism.is_valid():
                return f(mechanism.identity, *args, **kwargs)
        return reject()

    return decorated
