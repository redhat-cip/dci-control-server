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

import dci.app
from dci.db import models
from dci.elasticsearch import engine as es_engine
from dci.stores.swift import Swift
import tests.utils as utils
from dci.common import utils as dci_utils

from passlib.apps import custom_app_context as pwd_context
import contextlib
import pytest
import sqlalchemy
import sqlalchemy_utils.functions
import mock

import uuid

SWIFT = 'dci.stores.swift.Swift'


@pytest.fixture(scope='session')
def engine(request):
    utils.rm_upload_folder()
    db_uri = utils.conf['SQLALCHEMY_DATABASE_URI']

    engine = sqlalchemy.create_engine(db_uri)

    if not sqlalchemy_utils.functions.database_exists(db_uri):
        sqlalchemy_utils.functions.create_database(db_uri)
    utils.restore_db(engine)
    return engine


@pytest.fixture
def empty_db(engine):
    with contextlib.closing(engine.connect()) as con:
        meta = models.metadata
        trans = con.begin()
        for table in reversed(meta.sorted_tables):
            con.execute(table.delete())
        trans.commit()
    return True


@pytest.fixture
def reset_file_event(engine):
    with contextlib.closing(engine.connect()) as con:
        trans = con.begin()
        con.execute("ALTER SEQUENCE files_events_id_seq RESTART WITH 1")
        trans.commit()
    return True


@pytest.fixture
def delete_db(request, engine, teardown_db_clean):
    models.metadata.drop_all(engine)
    engine.execute("DROP TABLE IF EXISTS alembic_version")


@pytest.fixture(scope='session', autouse=True)
def memoize_password_hash():
    pwd_context.verify = utils.memoized(pwd_context.verify)
    pwd_context.encrypt = utils.memoized(pwd_context.encrypt)


@pytest.fixture
def teardown_db_clean(request, engine):
    request.addfinalizer(lambda: utils.restore_db(engine))


@pytest.fixture
def fs_clean(request):
    """Clean test file upload directory"""
    request.addfinalizer(utils.rm_upload_folder)


@pytest.fixture
def db_provisioning(empty_db, engine):
    with engine.begin() as conn:
        utils.provision(conn)


@pytest.fixture
def app(db_provisioning, engine, es_clean, fs_clean):
    app = dci.app.create_app(utils.conf)
    app.testing = True
    app.engine = engine
    return app


@pytest.fixture
def admin(app, db_provisioning):
    return utils.generate_client(app, ('admin', 'admin'))


@pytest.fixture
def admin_id(admin):
    team = admin.get('/api/v1/users?where=name:admin')
    team = admin.get('/api/v1/users/%s' % team.data['users'][0]['id']).data
    return str(team['user']['id'])


@pytest.fixture
def unauthorized(app, db_provisioning):
    return utils.generate_client(app, ('bob', 'bob'))


@pytest.fixture
def user(app, db_provisioning):
    return utils.generate_client(app, ('user', 'user'))


@pytest.fixture
def user_sso(app, db_provisioning, access_token):
    return utils.generate_client(app, access_token=access_token)


@pytest.fixture
def user_id(admin):
    team = admin.get('/api/v1/users?where=name:user')
    team = admin.get('/api/v1/users/%s' % team.data['users'][0]['id']).data
    return str(team['user']['id'])


@pytest.fixture
def user_admin(app, db_provisioning):
    return utils.generate_client(app, ('user_admin', 'user_admin'))


@pytest.fixture
def user_admin_id(admin):
    team = admin.get('/api/v1/users?where=name:user_admin')
    team = admin.get('/api/v1/users/%s' % team.data['users'][0]['id']).data
    return str(team['user']['id'])


@pytest.fixture
def product_owner(app, db_provisioning):
    return utils.generate_client(app, ('product_owner', 'product_owner'))


@pytest.fixture
def product_owner_id(admin):
    team = admin.get('/api/v1/users?where=name:product_owner')
    team = admin.get('/api/v1/users/%s' % team.data['users'][0]['id']).data
    return str(team['user']['id'])


@pytest.fixture
def topic_id(admin, team_id, product):
    data = {'name': 'topic_name', 'product_id': product['id'],
            'component_types': ['type_1', 'type_2', 'type_3']}
    topic = admin.post('/api/v1/topics', data=data).data
    t_id = topic['topic']['id']
    admin.post('/api/v1/topics/%s/teams' % t_id,
               data={'team_id': team_id,
                     'component_types': ['type_1', 'type_2', 'type_3']})
    return str(t_id)


@pytest.fixture
def topic(admin, team_user_id, product):
    topic = admin.post('/api/v1/topics', data={
        'name': 'OSP12',
        'product_id': product['id'],
        'component_types': ['puddle_osp']
    }).data['topic']
    admin.post('/api/v1/components', data={
        'topic_id': topic['id'],
        'name': 'RH7-RHOS-12.0 2017-11-09.2',
        'type': 'puddle_osp',
        'export_control': True
    })
    admin.post('/api/v1/topics/%s/teams' % topic['id'],
               data={'team_id': team_user_id})
    return topic


@pytest.fixture
def test_id(admin, team_id):
    data = {'name': 'pname', 'team_id': team_id}
    test = admin.post('/api/v1/tests', data=data).data
    return str(test['test']['id'])


@pytest.fixture
def test_user_id(admin, team_user_id):
    data = {'name': 'pname', 'team_id': team_user_id}
    test = admin.post('/api/v1/tests', data=data).data
    return str(test['test']['id'])


@pytest.fixture
def team_id(admin):
    team = admin.post('/api/v1/teams', data={'name': 'pname'}).data
    return str(team['team']['id'])


@pytest.fixture
def team_product_id(admin):
    team = admin.get('/api/v1/teams?where=name:product')
    team = admin.get('/api/v1/teams/%s' % team.data['teams'][0]['id']).data
    return str(team['team']['id'])


@pytest.fixture
def team_user_id(admin):
    team = admin.get('/api/v1/teams?where=name:user')
    team = admin.get('/api/v1/teams/%s' % team.data['teams'][0]['id']).data
    return str(team['team']['id'])


@pytest.fixture
def team_admin_id(admin):
    team = admin.get('/api/v1/teams?where=name:admin')
    team = admin.get('/api/v1/teams/%s' % team.data['teams'][0]['id']).data
    return str(team['team']['id'])


@pytest.fixture
def topic_user_id(admin, user, team_user_id, product):
    data = {'name': 'topic_user_name', 'product_id': product['id'],
            'component_types': ['type_1', 'type_2', 'type_3']}
    topic = admin.post('/api/v1/topics', data=data).data
    t_id = topic['topic']['id']
    admin.post('/api/v1/topics/%s/teams' % t_id,
               data={'team_id': team_user_id})
    return str(t_id)


@pytest.fixture
def remoteci_id(admin, team_id):
    data = {'name': 'pname', 'team_id': team_id, 'allow_upgrade_job': True}
    remoteci = admin.post('/api/v1/remotecis', data=data).data
    return str(remoteci['remoteci']['id'])


@pytest.fixture
def remoteci_user_api_secret(user, remoteci_user_id):
    api_secret = user.get('/api/v1/remotecis/%s' % remoteci_user_id).data
    return api_secret['remoteci']['api_secret']


@pytest.fixture
def remoteci_user_id(user, team_user_id):
    data = {'name': 'rname', 'team_id': team_user_id,
            'allow_upgrade_job': True}
    remoteci = user.post('/api/v1/remotecis', data=data).data
    return str(remoteci['remoteci']['id'])


@pytest.fixture
def remoteci(admin, team_id):
    data = {'name': 'remoteci', 'team_id': team_id, 'allow_upgrade_job': True}
    return admin.post('/api/v1/remotecis', data=data).data['remoteci']


@pytest.fixture
def remoteci_context(app, remoteci_user_id, remoteci_user_api_secret):
    return utils.generate_remoteci_client(app,
                                          remoteci_user_api_secret,
                                          remoteci_user_id)


@pytest.fixture
def remoteci_configuration_user_id(user, remoteci_user_id, topic_user_id):
    rc = user.post('/api/v1/remotecis/%s/configurations' % remoteci_user_id,
                   data={'name': 'cname',
                         'topic_id': topic_user_id,
                         'component_types': ['kikoo', 'lol'],
                         'data': {'lol': 'lol'}}).data
    return str(rc['configuration']['id'])


def create_components(user, topic_id, component_types):
    component_ids = []
    for ct in component_types:
        data = {'topic_id': topic_id,
                'name': 'name-' + str(uuid.uuid4()),
                'type': ct,
                'export_control': True}
        cmpt = user.post('/api/v1/components', data=data).data
        component_ids.append(str(cmpt['component']['id']))
    return component_ids


@pytest.fixture
def components_ids(admin, topic_id):
    component_types = ['type_1', 'type_2', 'type_3']
    return create_components(admin, topic_id, component_types)


@pytest.fixture
def components_user_ids(admin, topic_user_id):
    component_types = ['type_1', 'type_2', 'type_3']
    return create_components(admin, topic_user_id, component_types)


@pytest.fixture
def job_user_id(remoteci_context, remoteci_user_id, components_user_ids,
                topic_user_id):
    data = {'remoteci_id': remoteci_user_id,
            'components_ids': components_user_ids,
            'topic_id': topic_user_id}
    job = remoteci_context.post('/api/v1/jobs/schedule', data=data).data
    return job['job']['id']


@pytest.fixture
def jobstate_user_id(user, job_user_id):
    data = {'job_id': job_user_id, 'status': 'running', 'comment': 'kikoolol'}
    jobstate = user.post('/api/v1/jobstates', data=data).data
    return jobstate['jobstate']['id']


@pytest.fixture
def file_user_id(user, jobstate_user_id, team_user_id):
    with mock.patch(SWIFT, spec=Swift) as mock_swift:
        mockito = mock.MagicMock()

        head_result = {
            'etag': dci_utils.gen_etag(),
            'content-type': "stream",
            'content-length': 1
        }

        mockito.head.return_value = head_result
        mock_swift.return_value = mockito
        headers = {'DCI-JOBSTATE-ID': jobstate_user_id,
                   'DCI-NAME': 'name'}
        file = user.post('/api/v1/files',
                         headers=headers, data='kikoolol').data
        headers['team_id'] = team_user_id
        headers['id'] = file['file']['id']
        conn = es_engine.DCIESEngine(utils.conf)
        conn.index(headers)
        return file['file']['id']


@pytest.fixture
def file_job_user_id(user, job_user_id, team_user_id):
    with mock.patch(SWIFT, spec=Swift) as mock_swift:
        mockito = mock.MagicMock()

        head_result = {
            'etag': dci_utils.gen_etag(),
            'content-type': "stream",
            'content-length': 1
        }

        mockito.head.return_value = head_result
        mock_swift.return_value = mockito
        headers = {'DCI-JOB-ID': job_user_id,
                   'DCI-NAME': 'name'}
        file = user.post('/api/v1/files', headers=headers, data='foobar').data
        headers['team_id'] = team_user_id
        headers['id'] = file['file']['id']
        conn = es_engine.DCIESEngine(utils.conf)
        conn.index(headers)
        return file['file']['id']


@pytest.fixture
def role(admin):
    data = {
        'name': 'Manager',
        'label': 'MANAGER',
        'description': 'A Manager role',
    }
    role = admin.post('/api/v1/roles', data=data).data
    return role['role']


@pytest.fixture
def feeder(admin, team_product_id):
    data = {
        'name': 'random-name-feeder',
        'team_id': team_product_id,
    }
    feeder = admin.post('/api/v1/feeders', data=data).data
    return feeder['feeder']


@pytest.fixture
def permission(admin):
    data = {
        'name': 'A Permission',
        'label': 'APERMISSION',
        'description': 'This is a regular permission',
    }
    return admin.post('/api/v1/permissions', data=data).data['permission']


@pytest.fixture
def product_openstack(admin, team_id):
    data = {
        'name': 'OpenStack',
        'label': 'OPENSTACK',
        'description': 'Red Hat OpenStack Platform',
        'team_id': team_id
    }
    return admin.post('/api/v1/products', data=data).data['product']


@pytest.fixture
def product(admin):
    return admin.get('/api/v1/products?where=label:AWSM').data['products'][0]


@pytest.fixture
def es_clean(request):
    conn = es_engine.DCIESEngine(utils.conf)
    conn.cleanup()


@pytest.fixture
def role_super_admin(admin):
    return admin.get('/api/v1/roles?where=label:SUPER_ADMIN').data['roles'][0]


@pytest.fixture
def role_product_owner(admin):
    return admin.get(
        '/api/v1/roles?where=label:PRODUCT_OWNER'
    ).data['roles'][0]


@pytest.fixture
def role_admin(admin):
    return admin.get('/api/v1/roles?where=label:ADMIN').data['roles'][0]


@pytest.fixture
def role_user(admin):
    return admin.get('/api/v1/roles?where=label:USER').data['roles'][0]


@pytest.fixture
def role_remoteci(admin):
    return admin.get('/api/v1/roles?where=label:REMOTECI').data['roles'][0]


@pytest.fixture
def access_token():
    """
{
  "alg": "RS256",
  "typ": "JWT",
  "kid": "-68W8qbt5ztlVv4gemEWKwMeZQLVbs3ALVe4kNXdT8E"
}
{
  "jti": "bfff129a-f7f0-475e-9df4-f157f2f78ba7",
  "exp": 1505565718,
  "nbf": 0,
  "iat": 1505564818,
  "iss": "http://localhost:8180/auth/realms/dci-test",
  "aud": "dci-cs",
  "sub": "b309e4da-ed6f-45fc-9054-7855e6e4eb92",
  "typ": "Bearer",
  "azp": "dci-cs",
  "nonce": "ab40edba-9187-11e7-a921-c85b7636c33f",
  "auth_time": 1505564818,
  "session_state": "c5f689c8-66ad-41cc-b704-4d5ff9427152",
  "acr": "1",
  "allowed-origins": [
    "http://localhost:5000"
  ],
  "realm_access": {
    "roles": [
      "uma_authorization"
    ]
  },
  "resource_access": {
    "account": {
      "roles": [
        "manage-account",
        "manage-account-links",
        "view-profile"
      ]
    }
  },
  "email": "dci@distributed-ci.io",
  "username": "dci"
}
    """

    access_token = 'eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICItNjhX' \
        'OHFidDV6dGxWdjRnZW1FV0t3TWVaUUxWYnMzQUxWZTRrTlhkVDhFIn0.eyJqdGkiOiJ' \
        'iZmZmMTI5YS1mN2YwLTQ3NWUtOWRmNC1mMTU3ZjJmNzhiYTciLCJleHAiOjE1MDU1Nj' \
        'U3MTgsIm5iZiI6MCwiaWF0IjoxNTA1NTY0ODE4LCJpc3MiOiJodHRwOi8vbG9jYWxob' \
        '3N0OjgxODAvYXV0aC9yZWFsbXMvZGNpLXRlc3QiLCJhdWQiOiJkY2ktY3MiLCJzdWIi' \
        'OiJiMzA5ZTRkYS1lZDZmLTQ1ZmMtOTA1NC03ODU1ZTZlNGViOTIiLCJ0eXAiOiJCZWF' \
        'yZXIiLCJhenAiOiJkY2ktY3MiLCJub25jZSI6ImFiNDBlZGJhLTkxODctMTFlNy1hOT' \
        'IxLWM4NWI3NjM2YzMzZiIsImF1dGhfdGltZSI6MTUwNTU2NDgxOCwic2Vzc2lvbl9zd' \
        'GF0ZSI6ImM1ZjY4OWM4LTY2YWQtNDFjYy1iNzA0LTRkNWZmOTQyNzE1MiIsImFjciI6' \
        'IjEiLCJhbGxvd2VkLW9yaWdpbnMiOlsiaHR0cDovL2xvY2FsaG9zdDo1MDAwIl0sInJ' \
        'lYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJ1bWFfYXV0aG9yaXphdGlvbiJdfSwicmVzb3' \
        'VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiL' \
        'CJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sImVtYWlsIjoi' \
        'ZGNpQGRpc3RyaWJ1dGVkLWNpLmlvIiwidXNlcm5hbWUiOiJkY2kifQ.Sv-r1bChnDLQ' \
        'I1S9j07UJ3nYInu0grJS6_tCznLG2gW3_QXQhpLNKiMpNlyJU7hDQHXmRG7d2Y58JXF' \
        'RPLgDFMGnUeTyGxSJS2PcZ6WKKDLMdOnfqexKJfSqU17jJ7h18qeRjLWdK-PMLJAQkJ' \
        'u9QlqaQsZNIXH_2uYY1_rWeaulPia_fj6iNzmYxeUvqci2IBbRIrZV5lvxlL55v1siG' \
        '4vF26G8pbjGL7Fg7HvDekJCTZE5uWRCQtg15IJ44Fsspip6C2kSIhAFvsitFe5r7ltO' \
        'Nnh5nbZCsru5r9qEEYzcSyIZnkyVGgZrxNY_PY8CC6WtSBZTC7inFFcWWKioSw'
    return access_token
