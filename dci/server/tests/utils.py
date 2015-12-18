# -*- encoding: utf-8 -*-
#
# Copyright 2015 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import base64
import collections
import flask

from dci.server import auth
from dci.server.common import utils
from dci.server.db import models

# convenient alias
memoized = utils.memoized


def generate_client(app, credentials):
    attrs = ['status_code', 'data', 'headers']
    Response = collections.namedtuple('Response', attrs)

    token = (base64.b64encode(('%s:%s' % credentials).encode('utf8'))
             .decode('utf8'))
    headers = {
        'Authorization': 'Basic ' + token,
        'Content-Type': 'application/json'
    }

    def client_open_decorator(func):
        def wrapper(*args, **kwargs):
            data = kwargs.get('data')
            if data:
                kwargs['data'] = flask.json.dumps(data, cls=utils.JSONEncoder)

            headers.update(kwargs.get('headers', {}))
            kwargs['headers'] = headers
            response = func(*args, **kwargs)
            return Response(
                response.status_code, flask.json.loads(response.data or "{}"),
                response.headers
            )

        return wrapper

    client = app.test_client()
    client.open = client_open_decorator(client.open)

    return client


def provision(db_conn):
    def db_insert(model_item, **kwargs):
        query = model_item.insert().values(**kwargs)
        return db_conn.execute(query).inserted_primary_key[0]

    user_pw_hash = auth.hash_password('user')
    user_admin_pw_hash = auth.hash_password('user_admin')
    admin_pw_hash = auth.hash_password('admin')

    # Create teams
    team_admin_id = db_insert(models.TEAMS, name='admin')
    team_user_id = db_insert(models.TEAMS, name='user')

    # Create users
    db_insert(models.USERS,
              name='user',
              role='user',
              password=user_pw_hash,
              team_id=team_user_id)

    db_insert(models.USERS,
              name='user_admin',
              role='admin',
              password=user_admin_pw_hash,
              team_id=team_user_id)

    db_insert(models.USERS,
              name='admin',
              role='admin',
              password=admin_pw_hash,
              team_id=team_admin_id)
