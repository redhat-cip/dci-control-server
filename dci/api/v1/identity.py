# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Red Hat, Inc
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


@api.route('/identity', methods=['GET'])
@decorators.login_required
@decorators.check_roles
def get_identity(identity):
    """Returns some information about the currently authenticated identity"""
    return flask.Response(
        json.dumps(
            {
                'identity': {
                    'id': identity.id,
                    'name': identity.name,
                    'team_id': identity.team_id,
                    'team_name': identity.team_name,
                    'role_id': identity.role_id,
                    'role_label': identity.role_label,
                }
            }
        ), 200,
        headers={'ETag': identity.etag},
        content_type='application/json'
    )
