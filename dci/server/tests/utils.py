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

import uuid

from dci.server import auth2
from dci.server.common import utils
from dci.server.db import models_core


def create_component(
        client,
        name='bob',
        data={'component_keys': {'foo': ['bar1', 'bar2']}}):
    _, component_type, _ = client.post(
        '/api/componenttypes',
        data={'name': str(uuid.uuid4())}
    )
    component = client.post(
        '/api/components',
        data={
            'name': name,
            'canonical_project_name': 'this_is_something',
            'componenttype_id': component_type['id'],
            'data': data
        }
    )

    return component


def create_test(client):
    return client.post(
        '/api/tests',
        data={
            'name': 'bob',
            'data': {'test_keys': {'foo': ['bar1', 'bar2']}}
        })


def create_jobdefinition(client, test_id, priority=0, name='bob'):
    return client.post(
        '/api/jobdefinitions',
        data={'name': name,
              'test_id': test_id,
              'priority': priority}
    )


def create_jobdefinition_component(client, jobdefinition_id, component_id):
    return client.post(
        '/api/jobdefinition_components',
        data={
            'jobdefinition_id': jobdefinition_id,
            'component_id': component_id
        }
    )


def create_jobstate(client, job_id, status='ongoing'):
    return client.post(
        '/api/jobstates',
        data={'job_id': job_id, 'status': status}
    )


def create_file(client, jobstate_id):
    return client.post(
        '/api/files',
        data={'content': 'bob', 'name': 'bob', 'jobstate_id': jobstate_id}
    )


def create_remoteci(client):
    return client.post(
        '/api/remotecis',
        data={
            'name': 'a_remoteci',
            'data': {'remoteci_keys': {'foo': ['bar1', 'bar2']}}
        }
    )


def create_job(client, remoteci_id, recheck=False, job_id=None):
    path = '/api/jobs'
    if recheck:
        path = '/api/jobs?recheck=1&job_id=%s' % job_id
    return client.post(path, data={'remoteci_id': remoteci_id,
                                   'recheck': recheck})


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
                kwargs['data'] = flask.json.dumps(data,
                                                  default=utils.json_encoder)

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

    # Create teams
    team_admin_id = db_insert(models_core.TEAMS, name='admin')
    company_a_id = db_insert(models_core.TEAMS, name='company_a')
    company_b_id = db_insert(models_core.TEAMS, name='company_b')
    team_user_id = db_insert(models_core.TEAMS, name='user')

    # Create users
    user_pw_hash = auth2.hash_password('user')
    db_insert(models_core.USERS,
              name='user',
              role='user',
              password=user_pw_hash,
              team_id=team_user_id)

    user_admin_pw_hash = auth2.hash_password('user_admin')
    db_insert(models_core.USERS,
              name='user_admin',
              role='admin',
              password=user_admin_pw_hash,
              team_id=team_user_id)

    admin_pw_hash = auth2.hash_password('admin')
    admin_user_id = db_insert(models_core.USERS,
                              name='admin',
                              role='admin',
                              password=admin_pw_hash,
                              team_id=team_admin_id)

    company_a_pw_hash = auth2.hash_password('company_a_user')
    company_a_user_id = db_insert(models_core.USERS,
                                  name='company_a_user',
                                  password=company_a_pw_hash,
                                  team_id=company_a_id)

    company_b_pw_hash = auth2.hash_password('company_b_user')
    company_b_user_id = db_insert(models_core.USERS,
                                  name='company_b_user',
                                  password=company_b_pw_hash,
                                  team_id=company_b_id)

    # Create roles
    role_admin_id = db_insert(models_core.ROLES, name='admin')
    role_partner_id = db_insert(models_core.ROLES, name='partner')

    # Create user_roles
    db_insert(models_core.JOIN_USERS_ROLES, user_id=admin_user_id,
              role_id=role_admin_id)
    db_insert(models_core.JOIN_USERS_ROLES, user_id=admin_user_id,
              role_id=role_partner_id)
    db_insert(models_core.JOIN_USERS_ROLES, user_id=company_a_user_id,
              role_id=role_partner_id)
    db_insert(models_core.JOIN_USERS_ROLES, user_id=company_b_user_id,
              role_id=role_partner_id)
