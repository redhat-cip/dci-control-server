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

import dci.server.app
from dci.server.db import models
from dci.server import dci_config
from dci.server.tests import db_provision_test
import dci.server.tests.utils as utils

from passlib.apps import custom_app_context as pwd_context
import pytest
import sqlalchemy
import sqlalchemy_utils.functions


@pytest.fixture(scope='session')
def engine(request):
    conf = dci_config.generate_conf()
    db_uri = conf['SQLALCHEMY_DATABASE_URI']

    engine = sqlalchemy.create_engine(db_uri)

    def del_db():
        if sqlalchemy_utils.functions.database_exists(db_uri):
            sqlalchemy_utils.functions.drop_database(db_uri)

    del_db()
    request.addfinalizer(del_db)
    sqlalchemy_utils.functions.create_database(db_uri)

    models.metadata.create_all(engine)
    return engine


@pytest.fixture(scope='session', autouse=True)
def memoize_password_hash():
    pwd_context.verify = utils.memoized(pwd_context.verify)
    pwd_context.encrypt = utils.memoized(pwd_context.encrypt)


@pytest.fixture
def db_clean(request, engine):
    def fin():
        for table in reversed(models.metadata.sorted_tables):
            engine.execute(table.delete())
    request.addfinalizer(fin)


@pytest.fixture
def db_provisioning(db_clean, engine):
    with engine.begin() as conn:
        db_provision_test.provision(conn)


@pytest.fixture
def app(db_provisioning, engine):
    app = dci.server.app.create_app(dci_config.generate_conf())
    app.testing = True
    app.engine = engine
    return app


@pytest.fixture
def admin(app, db_provisioning):
    return utils.generate_client(app, ('admin', 'admin'))


@pytest.fixture
def company_a_user(app, db_provisioning):
    return utils.generate_client(app, ('company_a_user', 'company_a_user'))


@pytest.fixture
def company_b_user(app, db_provisioning):
    return utils.generate_client(app, ('company_b_user', 'company_b_user'))


@pytest.fixture
def unauthorized(app, db_provisioning):
    return utils.generate_client(app, ('admin', 'bob'))


@pytest.fixture
def user(app, db_provisioning):
    return utils.generate_client(app, ('user', 'user'))


@pytest.fixture
def user_admin(app, db_provisioning):
    return utils.generate_client(app, ('user_admin', 'user_admin'))


@pytest.fixture
def componenttype_id(admin):
    pct = admin.post('/api/v1/componenttypes',
                     data={'name': 'pname'}).data
    return pct['componenttype']['id']


@pytest.fixture
def test_id(admin):
    test = admin.post('/api/v1/tests', data={'name': 'pname'}).data
    return test['test']['id']


@pytest.fixture
def team_id(admin):
    team = admin.post('/api/v1/teams', data={'name': 'pname'}).data
    return team['team']['id']


@pytest.fixture
def team_user_id(admin):
    team = admin.get('/api/v1/teams/user').data
    return team['team']['id']


@pytest.fixture
def team_admin_id(admin):
    team = admin.get('/api/v1/teams/admin').data
    return team['team']['id']


@pytest.fixture
def remoteci_user_id(user, team_user_id):
    remoteci = user.post('/api/v1/remotecis',
                         data={'name': 'rname',
                               'team_id': team_user_id}).data
    return remoteci['remoteci']['id']


@pytest.fixture
def remoteci_id(admin, team_id):
    remoteci = admin.post('/api/v1/remotecis',
                          data={'name': 'pname',
                                'team_id': team_id}).data
    return remoteci['remoteci']['id']


@pytest.fixture
def jobdefinition_id(admin, test_id):
    jd = admin.post('/api/v1/jobdefinitions',
                    data={'name': 'pname', 'test_id': test_id}).data
    return jd['jobdefinition']['id']


@pytest.fixture
def job_id(admin, jobdefinition_id, team_id, remoteci_id):
    job = admin.post('/api/v1/jobs',
                     data={'jobdefinition_id': jobdefinition_id,
                           'team_id': team_id,
                           'remoteci_id': remoteci_id}).data
    return job['job']['id']


@pytest.fixture
def job_user_id(admin, jobdefinition_id, team_user_id, remoteci_user_id):
    job = admin.post('/api/v1/jobs',
                     data={'jobdefinition_id': jobdefinition_id,
                           'team_id': team_user_id,
                           'remoteci_id': remoteci_user_id}).data
    return job['job']['id']


@pytest.fixture
def jobstate_id(admin, job_id, team_id):
    jobstate = admin.post('/api/v1/jobstates',
                          data={'job_id': job_id, 'team_id': team_id,
                                'status': 'ongoing',
                                'comment': 'kikoolol'}).data
    return jobstate['jobstate']['id']


@pytest.fixture
def file_id(admin, jobstate_id, team_id):
    file = admin.post('/api/v1/files',
                      data={'jobstate_id': jobstate_id,
                            'team_id': team_id,
                            'content': 'kikoolol', 'name': 'name'}).data
    return file['file']['id']


@pytest.fixture
def jobstate_user_id(user, job_user_id, team_user_id):
    jobstate = user.post('/api/v1/jobstates',
                         data={'job_id': job_user_id,
                               'team_id': team_user_id,
                               'status': 'ongoing',
                               'comment': 'kikoolol'}).data
    return jobstate['jobstate']['id']
