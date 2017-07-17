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

from dci.auth_mechanism import BasicAuthMechanism, SignatureAuthMechanism


def reject():
    """Sends a 401 reject response that enables basic auth."""

    auth_message = ('Could not verify your access level for that URL.'
                    'Please login with proper credentials.')
    auth_message = json.dumps({'_status': 'Unauthorized',
                               'message': auth_message})

    headers = {'WWW-Authenticate': 'Basic realm="Login required"'}
    return flask.Response(auth_message, 401, headers=headers,
                          content_type='application/json')


def _login_required():
    for mechanism in [BasicAuthMechanism(flask.request),
                      SignatureAuthMechanism(flask.request)]:
        if mechanism.is_valid():
            return mechanism.identity

    return None


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        identity = _login_required()
        if identity:
            return f(identity, *args, **kwargs)
        return reject()

    return decorated
