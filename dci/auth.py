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
import sqlalchemy

from dci.auth_mechanism import BasicAuthMechanism
from dci.common import exceptions as exc
from dci.common import token
from dci.db import models

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
        for mechanism in [BasicAuthMechanism(flask.request)]:
            if mechanism.is_valid():
                return f(mechanism.identity, *args, **kwargs)
        return reject()

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


def _verify_remoteci_auth_signature(client_id, auth_signature):
    remoteci = _get_remoteci(client_id['id'])
    if remoteci is None:
        return None, False

    if remoteci.api_secret is None:
        return remoteci, False

    # local_digest = token._digest_request(
    #     remoteci.api_secret,
    #     flask.request).hexdigest()
    # flask.current_app.logger.debug('Digest was: %s' % local_digest)
    rq = flask.request
    # query_string = rq.full_path[len(rq.path) + 1:]
    url = rq.path.encode('utf-8')
    query_string = rq.query_string

    return remoteci, token.is_signature_valid(
        auth_signature,
        remoteci.api_secret, rq.method, rq.headers.get['Content-Type'],
        client_id['timestamp'], url, query_string, rq.data)


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


def requires_remoteci_signature(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        try:
            client_id = token.parse_client_id(
                flask.request.headers.get('DCI-Client-ID', ''))
        except ValueError as e:
            return reject_signature(e.message)

        request_digest = flask.request.headers.get('DCI-Auth-Signature')

        remoteci, auth_ok = _verify_remoteci_auth_signature(client_id,
                                                            request_digest)
        if not auth_ok:
            return reject_signature('Signature could not be verified: %s' %
                                    request_digest)

        remoteci = dict(remoteci)
        # NOTE(fc): this should be moved in another abstraction layer
        remoteci['role'] = 'remoteci'
        return func(remoteci, *args, **kwargs)
    return decorated
