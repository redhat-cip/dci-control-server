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

import flask
from functools import wraps
import hashlib
import hmac
import json
from passlib.apps import custom_app_context as pwd_context
import sqlalchemy.sql

from dci.common import exceptions as exc
from dci.db import models

UNAUTHORIZED = exc.DCIException('Operation not authorized.', status_code=401)


def hash_password(password):
    return pwd_context.encrypt(password)


def build_auth(username, password):
    """Check the combination username/password that is valid on the
    database.
    """

    where_clause = sqlalchemy.sql.expression.and_(
        models.USERS.c.name == username,
        models.USERS.c.state == 'active',
        models.TEAMS.c.state == 'active'
    )
    t_j = sqlalchemy.join(
        models.USERS, models.TEAMS,
        models.USERS.c.team_id == models.TEAMS.c.id)
    query_get_user = (sqlalchemy.sql
                      .select([
                          models.USERS,
                          models.TEAMS.c.name.label('team_name'),
                          models.TEAMS.c.country.label('team_country'),
                      ])
                      .select_from(t_j)
                      .where(where_clause))

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


def requires_auth(f):
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


def _get_remoteci(ci_id):
    """Get the remoteci including its API secret
    """
    where_clause = sqlalchemy.sql.expression.and_(
        models.REMOTECIS.c.id == ci_id,
        models.REMOTECIS.c.active is True,
        models.REMOTECIS.c.state == 'active',
        models.TEAMS.c.state == 'active'
    )
    join_clause = sqlalchemy.join(
        models.REMOTECIS, models.TEAMS,
        models.REMOTECIS.c.team_id == models.TEAMS.c.id
    )
    query = (sqlalchemy
             .select([
                 models.REMOTECIS,
                 models.TEAMS.c.name.label('team_name'),
                 models.TEAMS.c.country.label('team_country'),
             ])
             .select_from(join_clause)
             .where(where_clause))
    remoteci = flask.g.db_conn.execute(query).fetchone()
    return remoteci


def _verify_remoteci_auth_signature(remoteci_id, auth_signature):
    if remoteci_id is None:
        return reject_signature('Required parameter remoteci_id missing')

    remoteci = _get_remoteci(remoteci_id)
    if remoteci is None:
        return None, False

    if remoteci.api_secret is None:
        return remoteci, False

    local_digest = _digest_request(
        remoteci.api_secret,
        flask.request).hexdigest()
    flask.current_app.logger.debug('Digest was: %s' % local_digest)
    # NOTE(fc): hmac.compare_digest available in python≥(2.7,3.3)
    compare_digest = getattr(hmac, 'compare_digest',
                             lambda a, b: a == b)
    return remoteci, compare_digest(auth_signature, local_digest)


def _digest_request(secret, request):
    h = hmac.new(secret.encode(), digestmod=hashlib.sha256)
    h.update(request.url.encode(request.charset or 'utf-8'))
    if request.data:
        h.update(request.data.encode(request.charset or 'utf-8'))
    return h


def reject_signature(reason):
    """Sends a 401 reject response which asks for an auth token."""

    auth_message = ('Could not grant access for that URL. Reason:\n%s' %
                    reason)
    auth_message = json.dumps({'_status': 'Unauthorized',
                               'message': auth_message})

    headers = {
        'WWW-Authenticate': 'DCI-Client-ID and DCI-Auth-Signature required.',
    }
    return flask.Response(auth_message, 401, headers=headers,
                          content_type='application/json')


def require_remoteci_signature(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        request_digest = flask.request.headers.get(
            'DCI-Auth-Signature')
        flask.current_app.logger.debug('DCI-Auth-Signature: %s' %
                                       request_digest)

        remoteci_id = flask.request.headers.get('DCI-Client-ID')
        flask.current_app.logger.debug('Requested remoteci_id: %s' %
                                       remoteci_id)
        if remoteci_id is None:
            return reject_signature(
                'Required DCI-Client-ID header not found.')

        remoteci, auth_ok = _verify_remoteci_auth_signature(
            remoteci_id,
            request_digest)
        if not auth_ok:
            return reject('Signature could not be verified: %s' %
                          request_digest)

        remoteci = dict(remoteci)
        # NOTE(fc): this should be moved in another abstraction layer
        remoteci['remoteci'] = None
        return func(remoteci, *args, **kwargs)
