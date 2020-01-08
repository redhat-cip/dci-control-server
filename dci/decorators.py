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
import logging
from functools import wraps

import flask

import dci.auth_mechanism as am
from dci.common import exceptions as dci_exc

LOG = logging.getLogger(__name__)


def reject():
    """Sends a 401 reject response that enables basic auth."""

    auth_message = ('Could not verify your access level for that URL.'
                    'Please login with proper credentials.')
    auth_message = json.dumps({'_status': 'Unauthorized',
                               'message': auth_message})

    headers = {'WWW-Authenticate': 'Basic realm="Login required"'}
    LOG.info(auth_message)
    return flask.Response(auth_message, 401, headers=headers,
                          content_type='application/json')


def _get_auth_class_from_headers(headers):
    if 'Authorization' not in headers:
        raise dci_exc.DCIException('Authorization header missing',
                                   status_code=401)

    auth_type = headers.get('Authorization').split(' ')[0]
    if auth_type == 'Bearer':
        return am.OpenIDCAuth
    elif auth_type == 'DCI-HMAC-SHA256':
        return am.HmacMechanism
    elif auth_type in ['DCI2-HMAC-SHA256', 'AWS4-HMAC-SHA256']:
        return am.Hmac2Mechanism
    elif auth_type == 'Basic':
        return am.BasicAuthMechanism

    raise dci_exc.DCIException('Authorization scheme %s unknown' % auth_type,
                               status_code=401)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_class = _get_auth_class_from_headers(flask.request.headers)
        auth_scheme = auth_class(flask.request)
        auth_scheme.authenticate()
        return f(auth_scheme.identity, *args, **kwargs)

    return decorated
