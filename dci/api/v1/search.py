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
from flask import json

from dci.api.v1 import api
from dci import auth
from dci import decorators
from dci.common import schemas


@api.route('/search', methods=['POST'])
@decorators.login_required
@decorators.check_roles
def search(user):
    values = schemas.search.post(flask.request.json)

    if values['refresh']:
        flask.g.es_conn.refresh()

    if auth.is_admin(user):
        res = flask.g.es_conn.search_content(values['pattern'])
    else:
        res = flask.g.es_conn.search_content(values['pattern'],
                                             user['team_id'])

    result = json.jsonify({'logs': res['hits']})
    return result


@api.route('/search/<uuid:id>', methods=['GET'])
@decorators.login_required
@decorators.check_roles
def get_search_by_id(user, id):
    if auth.is_admin(user):
        res = flask.g.es_conn.get(id)
    else:
        res = flask.g.es_conn.get(id, user['team_id'])
    return json.jsonify({'logs': res})
