# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Red Hat, Inc
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

from dci.api.v1 import api
from dci import decorators


# TODO: replace this properly with JSONEncoder
def _encode_dict(_dict):
    res = {}
    for d in _dict:
        _values = {}
        for i in _dict[d]:
            _values[str(i)] = _dict[d][i]
        res[str(d)] = _values
    return res


@api.route('/identity', methods=['GET'])
@decorators.login_required
def get_identity(identity):
    """Returns some information about the currently authenticated identity"""
    return flask.Response(
        json.dumps(
            {
                'identity': {
                    'id': identity.id,
                    'etag': identity.etag,
                    'name': identity.name,
                    'fullname': identity.fullname,
                    'email': identity.email,
                    'timezone': identity.timezone,
                    'teams': _encode_dict(identity.teams)
                }
            }
        ), 200,
        headers={'ETag': identity.etag},
        content_type='application/json'
    )
