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

from dci.auth_mechanism import BasicAuthMechanism
from dci.common import exceptions as exc
from dci.db import models
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
# in place.
def super_admin_role_id():
    """Return Super Admin role id."""

    query = sql.select([models.ROLES]).where(
        models.ROLES.c.name == 'Super Admin'
    )
    result = flask.g.db_conn.execute(query).fetchone()
    return result.id


# This method should be deleted once permissions mechanism is
# in place.
def admin_role_id():
    """Return Admin role id."""

    query = sql.select([models.ROLES]).where(
        models.ROLES.c.name == 'Admin'
    )
    result = flask.g.db_conn.execute(query).fetchone()
    return result.id


def is_admin(user):
    return user['role_id'] == super_admin_role_id()


def is_admin_user(user, team_id):
    return str(user['team_id']) == str(team_id) and \
        user['role_id'] in [super_admin_role_id(), admin_role_id()]


def is_in_team(user, team_id):
    return str(user['team_id']) == str(team_id)


def check_export_control(user, component):
    if not is_admin(user):
        if not component['export_control']:
            raise UNAUTHORIZED


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        for mechanism in [BasicAuthMechanism(flask.request)]:
            if mechanism.is_valid():
                return f(mechanism.identity, *args, **kwargs)
        return reject()

    return decorated


def has_permission(permissions):
    """Check if the role the user belongs to has the proper permissions."""

    def check_permissions(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            for mechanism in [BasicAuthMechanism(flask.request)]:
                if mechanism.is_valid():

                    join = sql.join(
                        models.PERMISSIONS,
                        models.JOIN_ROLE_PERMISSIONS,
                        models.PERMISSIONS.c.id == models.JOIN_ROLE_PERMISSIONS.c.permission_id
                    )
                    query = sql.select([models.PERMISSIONS]).select_from(join).where(models.JOIN_ROLE_PERMISSIONS.c.role_id == str(mechanism.identity['role_id']))
                    rows = flask.g.db_conn.execute(query)
                    user_permissions = [dict(row)['value'] for row in rows]
                    for permission in permissions:
                        if permission in user_permissions:
                            return f(*args, **kwargs)
                    return reject()

        return decorated
    return check_permissions
