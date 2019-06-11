# -*- encoding: utf-8 -*-
#
# Copyright 2015-2016 Red Hat, Inc.
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

try:
    from urlparse import parse_qsl
    from urlparse import urlparse
except ImportError:
    from urllib.parse import parse_qsl
    from urllib.parse import urlparse
import base64
import collections
import flask
import shutil

import six

import dci.auth as auth
import dci.db.models as models
import dci.dci_config as config
from dci.common import utils
from dciauth.request import AuthRequest
from dciauth.signature import Signature

import os
import subprocess

# convenient alias
conf = config.generate_conf()


def restore_db(engine):
    models.metadata.drop_all(engine)
    models.metadata.create_all(engine)


def rm_upload_folder():
    shutil.rmtree(conf['FILES_UPLOAD_FOLDER'], ignore_errors=True)


def generate_client(app, credentials=None, access_token=None):
    attrs = ['status_code', 'data', 'headers']
    Response = collections.namedtuple('Response', attrs)

    if credentials:
        token = (base64.b64encode(('%s:%s' % credentials).encode('utf8'))
                 .decode('utf8'))
        headers = {
            'Authorization': 'Basic ' + token,
            'Content-Type': 'application/json'
        }
    elif access_token:
        headers = {
            'Authorization': 'Bearer ' + access_token,
            'Content-Type': 'application/json'
        }

    def client_open_decorator(func):
        def wrapper(*args, **kwargs):
            headers.update(kwargs.get('headers', {}))
            kwargs['headers'] = headers
            content_type = headers.get('Content-Type')
            data = kwargs.get('data')
            if data and content_type == 'application/json':
                kwargs['data'] = flask.json.dumps(data, cls=utils.JSONEncoder)
            response = func(*args, **kwargs)

            data = response.data
            if response.content_type == 'application/json':
                data = flask.json.loads(data or '{}')
            if type(data) == six.binary_type:
                data = data.decode('utf8')
            return Response(response.status_code, data, response.headers)

        return wrapper

    client = app.test_client()
    client.open = client_open_decorator(client.open)

    return client


def generate_token_based_client(app, resource):
    attrs = ['status_code', 'data', 'headers']
    Response = collections.namedtuple('Response', attrs)
    headers = {'Content-Type': 'application/json'}

    def client_open_decorator(func):
        def wrapper(*args, **kwargs):
            headers.update(kwargs.get('headers', {}))
            payload = kwargs.get('data')
            url = urlparse(args[0])
            params = dict(parse_qsl(url.query))
            auth_request = AuthRequest(
                method=kwargs.get('method'),
                endpoint=url.path,
                payload=payload,
                headers=headers,
                params=params
            )
            signature = Signature(request=auth_request)
            kwargs['headers'] = signature.generate_headers(
                client_id=resource['id'],
                client_type=resource['type'],
                secret=resource['api_secret']
            )
            if payload:
                json = flask.json.dumps(payload, cls=utils.JSONEncoder)
                kwargs['data'] = json
            response = func(*args, **kwargs)
            data = flask.json.loads(response.data or '{}')
            return Response(response.status_code, data, response.headers)

        return wrapper

    client = app.test_client()
    client.open = client_open_decorator(client.open)
    return client


def post_file(client, jobstate_id, file_desc, mime='text/plain'):
    headers = {'DCI-JOBSTATE-ID': jobstate_id, 'DCI-NAME': file_desc.name,
               'DCI-MIME': mime, 'Content-Type': 'text/plain'}
    res = client.post('/api/v1/files',
                      headers=headers,
                      data=file_desc.content)
    return res.data['file']['id']


def provision(db_conn):
    def db_insert(model_item, return_pk=True, **kwargs):
        query = model_item.insert().values(**kwargs)
        if return_pk:
            return db_conn.execute(query).inserted_primary_key[0]
        else:
            db_conn.execute(query)

    # Create teams
    team_admin_id = db_insert(models.TEAMS, name='admin')
    team_product_id = db_insert(models.TEAMS, name='product',
                                parent_id=team_admin_id)
    team_user_id = db_insert(models.TEAMS, name='user',
                             parent_id=team_product_id)
    db_insert(models.TEAMS, name='Red Hat')
    team_epm_id = db_insert(models.TEAMS, name='EPM')

    # Create users
    user_pw_hash = auth.hash_password('user')
    u_id = db_insert(models.USERS,
                     name='user',
                     sso_username='user',
                     password=user_pw_hash,
                     fullname='User',
                     email='user@example.org',
                     team_id=team_user_id)

    db_insert(models.JOIN_USERS_TEAMS_ROLES,
              return_pk=False,
              user_id=u_id,
              team_id=team_user_id,
              role='USER')

    user_no_team_pw_hash = auth.hash_password('user_no_team')
    u_id = db_insert(models.USERS,
                     name='user_no_team',
                     sso_username='user_no_team',
                     password=user_no_team_pw_hash,
                     fullname='User No Team',
                     email='user_no_team@example.org',
                     team_id=None)

    db_insert(models.JOIN_USERS_TEAMS_ROLES,
              return_pk=False,
              user_id=u_id,
              team_id=None,
              role='USER')

    product_owner_pw_hash = auth.hash_password('product_owner')
    u_id = db_insert(models.USERS,
                     name='product_owner',
                     sso_username='product_owner',
                     password=product_owner_pw_hash,
                     fullname='Product Owner',
                     email='product_ownern@example.org',
                     team_id=team_product_id)

    db_insert(models.JOIN_USERS_TEAMS_ROLES,
              return_pk=False,
              user_id=u_id,
              team_id=team_product_id,
              role='PRODUCT_OWNER')

    epm_pw_hash = auth.hash_password('epm')
    u_id = db_insert(models.USERS,
                     name='epm',
                     sso_username='epm',
                     password=epm_pw_hash,
                     fullname='Partner Engineer',
                     email='epm@redhat.com',
                     team_id=team_epm_id)

    db_insert(models.JOIN_USERS_TEAMS_ROLES,
              return_pk=False,
              user_id=u_id,
              team_id=team_epm_id,
              role='EPM')

    admin_pw_hash = auth.hash_password('admin')
    u_id = db_insert(models.USERS,
                     name='admin',
                     sso_username='admin',
                     password=admin_pw_hash,
                     fullname='Admin',
                     email='admin@example.org',
                     team_id=team_admin_id)

    db_insert(models.JOIN_USERS_TEAMS_ROLES,
              return_pk=False,
              user_id=u_id,
              team_id=team_admin_id,
              role='SUPER_ADMIN')

    # Create a product
    db_insert(models.PRODUCTS,
              name='Awesome product',
              label='AWSM',
              description='My Awesome product',
              team_id=team_product_id)

    # Create a product
    db_insert(models.PRODUCTS,
              name='Best product',
              label='BEST',
              description='My best product',
              team_id=team_product_id)


SWIFT = 'dci.stores.swift.Swift'

FileDesc = collections.namedtuple('FileDesc', ['name', 'content'])


def run_bin(bin_name, env):
    env.update(os.environ.copy())
    exec_path = os.path.abspath(__file__)
    exec_path = os.path.abspath('%s/../../bin/%s' % (exec_path, bin_name))
    return subprocess.Popen(exec_path, shell=True, env=env)
