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
from flask import json

from dci.server.api import exceptions


api = flask.Blueprint('api_v1', __name__)


@api.route('/', strict_slashes=False)
def index():
    return flask.Response(json.dumps({'_status': 'OK',
                                      'message': 'Distributed CI.'}),
                          status=200,
                          content_type='application/json')


@api.errorhandler(exceptions.ConflictError)
@api.errorhandler(exceptions.NotFound)
@api.errorhandler(exceptions.InternalError)
@api.errorhandler(exceptions.InvalidAPIUsage)
def handle_error(error):
    response = flask.jsonify(error.get_error())
    response.status_code = error.status_code
    return response


import dci.server.api.v1.componenttypes  # noqa
