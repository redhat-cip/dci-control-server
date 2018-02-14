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
from dci.elasticsearch import engine as elastic_engine
from dci.stores.swift import Swift
import tests.utils as utils
from dci.common import utils as dci_utils
import tests.sso_tokens as sso_tokens

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


@pytest.fixture(scope='session')
def es_engine(request):
    el_engine = elastic_engine.DCIESEngine(es_host=utils.conf['ES_HOST'],
                                           es_port=utils.conf['ES_PORT'],
                                           index='dci', timeout=60)

    def fin():
        el_engine.cleanup()
    request.addfinalizer(fin)
    return el_engine


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
def app(db_provisioning, engine, es_engine, fs_clean):
    app = dci.app.create_app(utils.conf, es_engine)
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
def user_sso(app, db_provisioning, access_token_rh_employee):
    return utils.generate_client(app, access_token=access_token_rh_employee)


@pytest.fixture
def user_sso_rh_employee(app, db_provisioning, access_token_rh_employee):
    return utils.generate_client(app, access_token=access_token_rh_employee)


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
    admin.post('/api/v1/topics/%s/teams' % t_id, data={'team_id': team_id})
    return str(t_id)


@pytest.fixture
def topic_id_product(product_owner, team_id, product):
    data = {'name': 'Ansible-2.4', 'product_id': product['id'],
            'component_types': ['git-commit']}
    topic = product_owner.post('/api/v1/topics', data=data).data
    t_id = topic['topic']['id']
    product_owner.post('/api/v1/topics/%s/teams' % t_id,
                       data={'team_id': team_id})
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
    remoteci = {'id': remoteci_user_id, 'api_secret': remoteci_user_api_secret,
                'type': 'remoteci'}
    return utils.generate_token_based_client(app, remoteci)


@pytest.fixture
def remoteci_configuration_user_id(user, remoteci_user_id, topic_user_id):
    rc = user.post('/api/v1/remotecis/%s/configurations' % remoteci_user_id,
                   data={'name': 'cname',
                         'topic_id': topic_user_id,
                         'component_types': ['kikoo', 'lol'],
                         'data': {'lol': 'lol'}}).data
    return str(rc['configuration']['id'])


@pytest.fixture
def feeder_id(product_owner, team_user_id):
    data = {'name': 'feeder_osp', 'team_id': team_user_id}
    feeder = product_owner.post('/api/v1/feeders', data=data).data
    return str(feeder['feeder']['id'])


@pytest.fixture
def feeder_api_secret(product_owner, feeder_id):
    api_secret = product_owner.get('/api/v1/feeders/%s' % feeder_id).data
    return api_secret['feeder']['api_secret']


@pytest.fixture
def feeder_context(app, feeder_id, feeder_api_secret):
    feeder = {'id': feeder_id, 'api_secret': feeder_api_secret,
              'type': 'feeder'}
    return utils.generate_token_based_client(app, feeder)


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
def job_user_id(remoteci_context, components_user_ids, topic_user_id):
    data = {'components_ids': components_user_ids,
            'topic_id': topic_user_id}
    job = remoteci_context.post('/api/v1/jobs/schedule', data=data).data
    return job['job']['id']


@pytest.fixture
def jobstate_user_id(user, job_user_id):
    data = {'job_id': job_user_id, 'status': 'running', 'comment': 'kikoolol'}
    jobstate = user.post('/api/v1/jobstates', data=data).data
    return jobstate['jobstate']['id']


@pytest.fixture
def file_user_id(user, jobstate_user_id, team_user_id, es_engine):
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
        es_engine.index(headers)
        return file['file']['id']


@pytest.fixture
def file_job_user_id(user, job_user_id, team_user_id, es_engine):
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
        es_engine.index(headers)
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
    return sso_tokens.ACCESS_TOKEN_USER


@pytest.fixture
def access_token_rh_employee():
    return sso_tokens.ACCESS_TOKEN_RH_EMPLOYEE
