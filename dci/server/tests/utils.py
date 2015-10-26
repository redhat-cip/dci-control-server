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


def create_component(
        client,
        name='bob',
        data={'component_keys': {'foo': ['bar1', 'bar2']}}):
    _, component_type, _ = client.post(
        '/api/componenttypes',
        data={'name': 'a_component_type'}
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
                kwargs['data'] = flask.json.dumps(data)

            headers.update(kwargs.get('headers', {}))
            kwargs['headers'] = headers
            response = func(*args, **kwargs)
            return Response(
                response.status_code, flask.json.loads(response.data),
                response.headers
            )

        return wrapper

    client = app.test_client()
    client.open = client_open_decorator(client.open)

    return client
