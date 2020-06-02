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
import tests.utils as utils
import tests.sso_tokens as sso_tokens

from passlib.apps import custom_app_context as pwd_context
import contextlib
import pytest
import sqlalchemy
import sqlalchemy_utils.functions

import uuid


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
def reset_job_event(engine):
    with contextlib.closing(engine.connect()) as con:
        trans = con.begin()
        con.execute("ALTER SEQUENCE jobs_events_id_seq RESTART WITH 1")
        trans.commit()
    return True


@pytest.fixture
def delete_db(request, engine, teardown_db_clean):
    models.metadata.drop_all(engine)
    engine.execute("DROP TABLE IF EXISTS alembic_version")


@pytest.fixture(scope='session', autouse=True)
def memoize_password_hash():
    def memoize(func):
        cache = {}

        def helper(*args):
            if args in cache:
                return cache[args]
            else:
                value = func(*args)
                cache[args] = value
                return value
        return helper
    pwd_context.verify = memoize(pwd_context.verify)
    pwd_context.encrypt = memoize(pwd_context.encrypt)


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
def app(db_provisioning, engine, fs_clean):
    app = dci.app.create_app()
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
    client = utils.generate_client(app, access_token=access_token)
    # first call, it create the user in the database
    client.get('/api/v1/users/me')
    return client


@pytest.fixture
def user_sso_rh_employee(app, db_provisioning, access_token_rh_employee):
    client = utils.generate_client(app, access_token=access_token_rh_employee)
    # first call, it create the user in the database
    client.get('/api/v1/users/me')
    return client


@pytest.fixture
def user_id(admin):
    user = admin.get('/api/v1/users?where=name:user')
    user = admin.get('/api/v1/users/%s' % user.data['users'][0]['id']).data
    return str(user['user']['id'])


@pytest.fixture
def user_no_team(admin):
    r = admin.get('/api/v1/users?where=name:user_no_team')
    return dict(r.data['users'][0])


@pytest.fixture
def epm(app, db_provisioning):
    return utils.generate_client(app, ('epm', 'epm'))


@pytest.fixture
def topic_id(admin, team_id, product):
    data = {'name': 'topic_name', 'product_id': product['id'],
            'component_types': ['type_1', 'type_2', 'type_3']}
    topic = admin.post('/api/v1/topics', data=data).data
    t_id = topic['topic']['id']
    admin.post('/api/v1/topics/%s/teams' % t_id, data={'team_id': team_id})
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
        'type': 'puddle_osp'
    })
    admin.post('/api/v1/topics/%s/teams' % topic['id'],
               data={'team_id': team_user_id})
    return topic


@pytest.fixture
def test_id(admin):
    data = {'name': 'pname'}
    test = admin.post('/api/v1/tests', data=data).data
    return str(test['test']['id'])


@pytest.fixture
def team_id(admin, team_user_id):
    team = admin.post('/api/v1/teams', data={'name': 'pname'})
    return str(team.data['team']['id'])


@pytest.fixture
def team_product_id(admin):
    team = admin.get('/api/v1/teams?where=name:product')
    team = admin.get('/api/v1/teams/%s' % team.data['teams'][0]['id']).data
    return str(team['team']['id'])


@pytest.fixture
def team_user_id(admin, product_id):
    team = admin.get('/api/v1/teams?where=name:user')
    team = admin.get('/api/v1/teams/%s' % team.data['teams'][0]['id']).data
    admin.post('/api/v1/products/%s/teams' % (product_id),
               data={'team_id': str(team['team']['id'])})
    return str(team['team']['id'])


@pytest.fixture
def team_admin_id(admin):
    team = admin.get('/api/v1/teams?where=name:admin')
    team = admin.get('/api/v1/teams/%s' % team.data['teams'][0]['id']).data
    return str(team['team']['id'])


@pytest.fixture
def team_redhat_id(admin):
    team = admin.get('/api/v1/teams?where=name:Red Hat')
    team = admin.get('/api/v1/teams/%s' % team.data['teams'][0]['id']).data
    return str(team['team']['id'])


@pytest.fixture
def team_epm_id(admin):
    team = admin.get('/api/v1/teams?where=name:EPM')
    team = admin.get('/api/v1/teams/%s' % team.data['teams'][0]['id']).data
    return str(team['team']['id'])


@pytest.fixture
def topic_user(admin, user, team_user_id, product):
    data = {'name': 'topic_user_name', 'product_id': product['id'],
            'component_types': ['type_1', 'type_2', 'type_3'],
            'export_control': True}
    topic = admin.post('/api/v1/topics', data=data).data
    t_id = topic['topic']['id']
    admin.post('/api/v1/topics/%s/teams' % t_id,
               data={'team_id': team_user_id})

    for i in range(1, 4):
        admin.post('/api/v1/components', data={
            'topic_id': t_id,
            'name': 'comp%s' % i,
            'type': 'type_%s' % i
        })

    return topic['topic']


@pytest.fixture
def topic_user_id(topic_user):
    return topic_user['id']


@pytest.fixture
def remoteci_id(admin, team_id):
    data = {'name': 'pname', 'team_id': team_id}
    remoteci = admin.post('/api/v1/remotecis', data=data).data
    return str(remoteci['remoteci']['id'])


@pytest.fixture
def remoteci_user_api_secret(user, remoteci_user_id):
    api_secret = user.get('/api/v1/remotecis/%s' % remoteci_user_id).data
    return api_secret['remoteci']['api_secret']


@pytest.fixture
def remoteci_user_id(user, admin, team_user_id, topic_user_id):
    data = {'name': 'rname', 'team_id': team_user_id}
    remoteci = user.post('/api/v1/remotecis', data=data).data

    return str(remoteci['remoteci']['id'])


@pytest.fixture
def remoteci(admin, team_id):
    data = {'name': 'remoteci', 'team_id': team_id}
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
def feeder_id(epm, team_user_id):
    data = {'name': 'feeder_osp', 'team_id': team_user_id}
    feeder = epm.post('/api/v1/feeders', data=data).data
    return str(feeder['feeder']['id'])


@pytest.fixture
def feeder_api_secret(epm, feeder_id):
    api_secret = epm.get('/api/v1/feeders/%s' % feeder_id).data
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
                'type': ct}
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
def file_user_id(user, jobstate_user_id, team_user_id):
    headers = {'DCI-JOBSTATE-ID': jobstate_user_id,
               'DCI-NAME': 'name'}
    file = user.post('/api/v1/files',
                     headers=headers, data='kikoolol').data
    headers['team_id'] = team_user_id
    headers['id'] = file['file']['id']
    return file['file']['id']


@pytest.fixture
def file_job_user_id(user, job_user_id, team_user_id):
    headers = {'DCI-JOB-ID': job_user_id,
               'DCI-NAME': 'name'}
    file = user.post('/api/v1/files', headers=headers, data='foobar').data
    headers['team_id'] = team_user_id
    headers['id'] = file['file']['id']
    return file['file']['id']


@pytest.fixture
def feeder(admin, team_product_id):
    data = {
        'name': 'random-name-feeder',
        'team_id': team_product_id,
    }
    feeder = admin.post('/api/v1/feeders', data=data).data
    return feeder['feeder']


@pytest.fixture
def product_openstack(admin, team_id):
    data = {
        'name': 'OpenStack',
        'label': 'OPENSTACK',
        'description': 'Red Hat OpenStack Platform'
    }
    return admin.post('/api/v1/products', data=data).data['product']


@pytest.fixture
def product(admin):
    return admin.get('/api/v1/products?where=label:AWSM').data['products'][0]


@pytest.fixture
def product2(admin):
    return admin.get('/api/v1/products?where=label:BEST').data['products'][0]


@pytest.fixture
def product_id(product):
    return str(product['id'])


@pytest.fixture
def access_token():
    return sso_tokens.ACCESS_TOKEN_USER


@pytest.fixture
def access_token_rh_employee():
    return sso_tokens.ACCESS_TOKEN_READ_ONLY_USER


@pytest.fixture(scope='session')
def cakeys():
    k = '-----BEGIN RSA PRIVATE KEY-----\n' \
        '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\n' \
        '-----END RSA PRIVATE KEY-----'
    c = '-----BEGIN CERTIFICATE-----\n' \
        'MIIF5jCCA86gAwIBAgIJAK1pLlYEf/ebMA0GCSqGSIb3DQEBCwUAMIGHMQswCQYD\n' \
        'VQQGEwJGUjEMMAoGA1UECAwDSURGMQ4wDAYDVQQHDAVQYXJpczEPMA0GA1UECgwG\n' \
        'UmVkSGF0MQwwCgYDVQQLDANEQ0kxETAPBgNVBAMMCERDSS1SZXBvMSgwJgYJKoZI\n' \
        'hvcNAQkBFhlkaXN0cmlidXRlZC1jaUByZWRoYXQuY29tMB4XDTE4MDMxNDEzMzY0\n' \
        'MFoXDTE5MDMxNDEzMzY0MFowgYcxCzAJBgNVBAYTAkZSMQwwCgYDVQQIDANJREYx\n' \
        'DjAMBgNVBAcMBVBhcmlzMQ8wDQYDVQQKDAZSZWRIYXQxDDAKBgNVBAsMA0RDSTER\n' \
        'MA8GA1UEAwwIRENJLVJlcG8xKDAmBgkqhkiG9w0BCQEWGWRpc3RyaWJ1dGVkLWNp\n' \
        'QHJlZGhhdC5jb20wggIiMA0GCSqGSIb3DQEBAQUAA4ICDwAwggIKAoICAQDFVjYL\n' \
        'h6zhjAy3DB7oUq7Jsxnwry5bKUXoBS6vMWenyZg5vBMi8zlbR6zuqN1PtSjBkEoL\n' \
        '7CIIV/Ab07odkmPrY9b898dElZslno9os8aPUnzepg1KhJYjHfjShSDNmeHSHdi5\n' \
        'yq3rfi2Mf72dGrli6YsMqtzGvJRKcaQXG/2NvHvJNQleXdAW7mmOhqbvyrpttmNB\n' \
        'qlMWqZKgo2SGl+WcuzFTWvbuWZ9ZSPRyGHVMFHScLGR2oJ1p8iXYxYIImHfLjn1C\n' \
        'bqdsME2t0Mylz7GW6uL/2j8w9YGTdqa/uq8TM6fYMjEfWf+curOwJ5HzoTNER6Yi\n' \
        'T7bn1BBNZCqyKrWuCEOXcIkHgNYd5zQLkUts6r3BC9VLwntQ0pCvFw/eefFrSI4Z\n' \
        'ZiehLOl+4H24og61Iw0mY/OcUCJRsxuNEsAKRZCUgd5XKqpwRcuYRF2khDwihk93\n' \
        'pEu1zyDtRiOmkyxt3fjaBwGqf62yRLkLcpruDqylgqEK3tMvdyaHlOOCGP2xN6ZQ\n' \
        '+wbyr1RVpQMiPkgc6DbaQ35NKhrkOyggRLbHaKOAteAsw/1a2Z9VXEr2YMqb0VUz\n' \
        'Am6oVTY6O8QvD93d4q99VMtlxnrjsFgzF9TEa2P1HnyPEHS4v+djjOHHCmDEsGrw\n' \
        '+/7HczAukYU6oCokU7qrneX13fikh63K4MSqqQIDAQABo1MwUTAdBgNVHQ4EFgQU\n' \
        'MAt4tfiBDZ7koyZq8Ss0P+swDpQwHwYDVR0jBBgwFoAUMAt4tfiBDZ7koyZq8Ss0\n' \
        'P+swDpQwDwYDVR0TAQH/BAUwAwEB/zANBgkqhkiG9w0BAQsFAAOCAgEAlqC46nbw\n' \
        'Y8UhIktSTInTrtX70Y9QF/Gl0weDoOgUNG/j9ReQPU1h/W3Ion4sZ4WO6Q3Y3jQ/\n' \
        '0+Ky0bJFpQZ0C3ssS65XdJC9fpLsiZY/HZUlgRuj7tnR7AjqHA6PBFNz83yGHZgq\n' \
        'GMA3LMq+FyY3K/FTj/NX5iaE2sJlDLu36yv6zcVnQwskkQ/rHoNmE3Prr3A7ZkLv\n' \
        'Ox73PpkiD7FySmTFiiz6i/CPUyx6Y9fZNhNSXvjg6F2tXYQWPJAEL0fWTKvywMML\n' \
        'tpIQnwz6hNaH5Z+O92X67LfJJtmoggNexmO/pbeGVNYPjyRllMcNNJq3GsABwzuA\n' \
        '7zIitCjqpw0RV40pSLv9oulqrS+tdMW55R/RxVCEx3L0H/L36K7IjXan5UkWQxlW\n' \
        'zi65LvYGgCU9d0CH7gUtyyRgJ1G7hAYbBqYOlMEjHdYYOGhGW4LVKSJ4QwPn+yHn\n' \
        '+GXELJTacwV0LVGcDPkqdWbt0KcyMukDFQXs5UikE3i+54783cmfZr3U5Gr/OCWZ\n' \
        'VikifhmBSl3sRfVm7YPW5pffAdACRDZVjZ6ro37x0JQ6jERuhaKe7sv3s0/gCWT5\n' \
        'XMFg+rftswcrSvxBpVNTUu5vPnXK3dWsM4noalVxh449ewlcruYh17Yt2KEwkB/+\n' \
        '4AMjw7GIwuUN1rZsqBbZ5tBHrRoR02IDcMA=\n' \
        '-----END CERTIFICATE-----'
    cert = open('/tmp/ca.crt', 'w')
    cert.write(c)
    cert.close()
    key = open('/tmp/ca.key', 'w')
    key.write(k)
    key.close()


@pytest.fixture
def RHELProduct(admin, team_id):
    data = {"name": "RHEL", "label": "RHEL", "description": "Red Hat Entreprise Linux"}
    return admin.post("/api/v1/products", data=data).data["product"]


@pytest.fixture
def RHEL80Topic(admin, RHELProduct):
    data = {
        "name": "RHEL-8.0",
        "product_id": RHELProduct["id"],
        "component_types": ["Compose"],
        "export_control": True,
    }
    return admin.post("/api/v1/topics", data=data).data["topic"]


@pytest.fixture
def RHEL80Component(admin, RHEL80Topic):
    data = {
        "topic_id": RHEL80Topic["id"],
        "name": "RHEL-8.0.0-20190926.n.0",
        "type": "Compose",
    }
    return admin.post("/api/v1/components", data=data).data["component"]


@pytest.fixture
def RHEL81Topic(admin, RHELProduct):
    data = {
        "name": "RHEL-8.1",
        "product_id": RHELProduct["id"],
        "component_types": ["Compose"],
        "export_control": False,
    }
    return admin.post("/api/v1/topics", data=data).data["topic"]


@pytest.fixture
def RHEL81Component(admin, RHEL81Topic):
    data = {
        "topic_id": RHEL81Topic["id"],
        "name": "RHEL-8.1.0-20190926.n.0",
        "type": "Compose",
    }
    return admin.post("/api/v1/components", data=data).data["component"]
