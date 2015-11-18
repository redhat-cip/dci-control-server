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
from __future__ import unicode_literals

import dci.server.common.schemas as schemas
import dci.server.tests.schemas.utils as utils
import flask
import voluptuous


def test_validation_error_handling(app):
    schema = schemas.Schema({voluptuous.Required('id'): str})
    app.add_url_rule('/test_validation_handling', view_func=lambda: schema({}))

    client = app.test_client()
    resp = client.get('/test_validation_handling')
    assert resp.status_code == 400
    assert flask.json.loads(resp.data) == {
        'status_code': 400,
        'message': 'Request malformed',
        'payload': {
            'errors': {'id': 'required key not provided'}
        }
    }


class BaseSchemaTesting(utils.SchemaTesting):

    data = dict([utils.NAME])

    def test_post_extra_data(self):
        super(BaseSchemaTesting, self).test_post_extra_data(self.data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name')
        super(BaseSchemaTesting, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        super(BaseSchemaTesting, self).test_post_invalid_data(
            dict([utils.INVALID_NAME]), dict([utils.INVALID_NAME_ERROR])
        )

    def test_post(self):
        super(BaseSchemaTesting, self).test_post(self.data, self.data)

    def test_put_extra_data(self):
        super(BaseSchemaTesting, self).test_put_extra_data(self.data)

    def test_put_invalid_data(self):
        data = dict([utils.INVALID_NAME])
        errors = dict([utils.INVALID_NAME_ERROR])

        super(BaseSchemaTesting, self).test_put_invalid_data(data, errors)

    def test_put(self):
        super(BaseSchemaTesting, self).test_put(self.data, self.data)


class TestComponentType(BaseSchemaTesting):
    schema = schemas.component_type


class TestTeam(BaseSchemaTesting):
    schema = schemas.team


class TestRole(BaseSchemaTesting):
    schema = schemas.role


class TestTest(utils.SchemaTesting):
    schema = schemas.test
    data = dict([utils.NAME])

    def test_post_extra_data(self):
        data = data_expected = utils.dict_merge(
            self.data, {'data': {'foo': {'bar': 'baz'}}}
        )
        super(TestTest, self).test_post(data, data_expected)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name')
        super(TestTest, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        data = dict([utils.INVALID_NAME, utils.INVALID_DATA])
        errors = dict([utils.INVALID_NAME_ERROR, utils.INVALID_DATA_ERROR])

        super(TestTest, self).test_post_invalid_data(data, errors)

    def test_post(self):
        super(TestTest, self).test_post(self.data, self.data)

    def test_put_extra_data(self):
        super(TestTest, self).test_put_extra_data(self.data)

    def test_put_invalid_data(self):
        data = dict([utils.INVALID_NAME, utils.INVALID_DATA])
        errors = dict([utils.INVALID_NAME_ERROR, utils.INVALID_DATA_ERROR])
        super(TestTest, self).test_put_invalid_data(data, errors)

    def test_put(self):
        super(TestTest, self).test_put(self.data, self.data)


class TestUser(utils.SchemaTesting):
    TEAM = 'team', utils.ID[1]
    INVALID_TEAM = 'team', utils.INVALID_ID
    INVALID_TEAM_ERROR = 'team', schemas.INVALID_TEAM

    schema = schemas.user
    data = dict([utils.NAME, utils.PASSWORD, TEAM])

    def test_post_extra_data(self):
        super(TestUser, self).test_post_extra_data(self.data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name', 'password', 'team')
        super(TestUser, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        data = dict([utils.INVALID_NAME, utils.INVALID_PASSWORD,
                     self.INVALID_TEAM])
        errors = dict([utils.INVALID_NAME_ERROR, self.INVALID_TEAM_ERROR,
                       utils.INVALID_PASSWORD_ERROR])

        super(TestUser, self).test_post_invalid_data(data, errors)

    def test_post(self):
        super(TestUser, self).test_post(self.data, self.data)

    def test_put_extra_data(self):
        super(TestUser, self).test_put_extra_data(self.data)

    def test_put_invalid_data(self):
        data = dict([utils.INVALID_NAME, utils.INVALID_PASSWORD,
                     self.INVALID_TEAM])
        errors = dict([utils.INVALID_NAME_ERROR, self.INVALID_TEAM_ERROR,
                       utils.INVALID_PASSWORD_ERROR])

        super(TestUser, self).test_put_invalid_data(data, errors)

    def test_put(self):
        super(TestUser, self).test_put(self.data, self.data)


class TestComponent(utils.SchemaTesting):
    COMPONENTTYPE = 'componenttype', utils.ID[1]
    INVALID_COMPONENTTYPE = 'componenttype', utils.INVALID_ID
    INVALID_COMPONENTTYPE_ERROR = ('componenttype',
                                   schemas.INVALID_COMPONENT_TYPE)

    schema = schemas.component
    data = dict([utils.NAME, COMPONENTTYPE])

    @staticmethod
    def generate_optionals():
        return dict([('sha', utils.text_type), ('title', utils.text_type),
                     ('message', utils.text_type), ('git', utils.text_type),
                     ('ref', utils.text_type),
                     ('canonical_project_name', utils.text_type)])

    @staticmethod
    def generate_optionals_errors():
        invalids = []
        errors = []
        for field in ['sha', 'title', 'message', 'git', 'ref',
                      'canonical_project_name']:
            invalid, error = utils.generate_invalid_string(field)
            invalids.append(invalid)
            errors.append(error)
        return invalids, errors

    def test_post_extra_data(self):
        super(TestComponent, self).test_post_extra_data(self.data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name', 'componenttype')
        super(TestComponent, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestComponent.generate_optionals_errors()

        data = dict([utils.INVALID_NAME, self.INVALID_COMPONENTTYPE,
                     utils.INVALID_DATA] + invalids)
        errors = dict([utils.INVALID_NAME_ERROR,
                       self.INVALID_COMPONENTTYPE_ERROR,
                       utils.INVALID_DATA_ERROR] + errors)

        super(TestComponent, self).test_post_invalid_data(data, errors)

    def test_post(self):
        data_expected = utils.dict_merge(self.data)
        super(TestComponent, self).test_post(self.data, data_expected)

    def test_put_extra_data(self):
        super(TestComponent, self).test_put_extra_data(self.data)

    def test_put_invalid_data(self):
        invalids, errors = TestComponent.generate_optionals_errors()
        data = dict([utils.INVALID_NAME, self.INVALID_COMPONENTTYPE,
                     utils.INVALID_DATA, utils.INVALID_URL] + invalids)

        errors = dict([utils.INVALID_NAME_ERROR, utils.INVALID_DATA_ERROR,
                       self.INVALID_COMPONENTTYPE_ERROR,
                       utils.INVALID_URL_ERROR] + errors)

        super(TestComponent, self).test_put_invalid_data(data, errors)

    def test_put(self):
        super(TestComponent, self).test_put(self.data, self.data)


class TestJobDefinition(utils.SchemaTesting):
    TEST = 'test', utils.ID[1]
    INVALID_TEST = 'test', utils.INVALID_ID
    INVALID_TEST_ERROR = 'test', schemas.INVALID_TEST
    INVALID_PRIORITY_ERROR = 'priority', schemas.INVALID_PRIORITY

    schema = schemas.jobdefinition
    data = dict([utils.NAME, TEST])

    def test_post_extra_data(self):
        data = utils.dict_merge(self.data, {'priority': 10})
        super(TestJobDefinition, self).test_post_extra_data(data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name', 'test')
        super(TestJobDefinition, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids = dict([utils.INVALID_NAME, self.INVALID_TEST,
                         ('priority', -1)])
        errors = dict([utils.INVALID_NAME_ERROR, self.INVALID_TEST_ERROR,
                       self.INVALID_PRIORITY_ERROR])

        super(TestJobDefinition, self).test_post_invalid_data(invalids, errors)
        invalids['priority'] = 1001
        super(TestJobDefinition, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        super(TestJobDefinition, self).test_post(self.data, self.data)

    def test_put_extra_data(self):
        super(TestJobDefinition, self).test_put_extra_data(self.data)

    def test_put_invalid_data(self):
        invalids = dict([utils.INVALID_NAME, self.INVALID_TEST,
                         ('priority', -1)])
        errors = dict([utils.INVALID_NAME_ERROR, self.INVALID_TEST_ERROR,
                       self.INVALID_PRIORITY_ERROR])

        super(TestJobDefinition, self).test_put_invalid_data(invalids, errors)
        invalids['priority'] = 1001
        super(TestJobDefinition, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        super(TestJobDefinition, self).test_put(self.data, self.data)


class TestRemoteCI(utils.SchemaTesting):
    TEST = 'test', utils.ID[1]
    INVALID_TEST = 'test', utils.INVALID_ID
    INVALID_TEST_ERROR = 'test', schemas.INVALID_TEST

    TEAM = 'team', utils.ID[1]
    INVALID_TEAM = 'team', utils.INVALID_ID
    INVALID_TEAM_ERROR = 'team', schemas.INVALID_TEAM

    schema = schemas.remoteci
    data = dict([utils.NAME, TEST, TEAM])

    def test_post_extra_data(self):
        data = data_expected = utils.dict_merge(
            self.data, {'data': {'foo': {'bar': 'baz'}}}
        )
        super(TestRemoteCI, self).test_post(data, data_expected)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name', 'test', 'team')
        super(TestRemoteCI, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids = dict([utils.INVALID_NAME, self.INVALID_TEST,
                         self.INVALID_TEAM])
        errors = dict([utils.INVALID_NAME_ERROR, self.INVALID_TEST_ERROR,
                       self.INVALID_TEAM_ERROR])

        super(TestRemoteCI, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        super(TestRemoteCI, self).test_post(self.data, self.data)

    def test_put_extra_data(self):
        super(TestRemoteCI, self).test_put_extra_data(self.data)

    def test_put_invalid_data(self):
        invalids = dict([utils.INVALID_NAME, self.INVALID_TEST,
                         self.INVALID_TEAM])
        errors = dict([utils.INVALID_NAME_ERROR, self.INVALID_TEST_ERROR,
                       self.INVALID_TEAM_ERROR])

        super(TestRemoteCI, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        super(TestRemoteCI, self).test_put(self.data, self.data)


class TestJob(utils.SchemaTesting):
    TEAM = 'team', utils.ID[1]
    INVALID_TEAM = 'team', utils.INVALID_ID
    INVALID_TEAM_ERROR = 'team', schemas.INVALID_TEAM

    JOB_DEFINITION = 'jobdefinition', utils.ID[1]
    INVALID_JOB_DEFINITION = 'jobdefinition', utils.INVALID_ID
    INVALID_JOB_DEFINITION_ERROR = ('jobdefinition',
                                    schemas.INVALID_JOB_DEFINITION)

    REMOTE_CI = 'remoteci', utils.ID[1]
    INVALID_REMOTE_CI = 'remoteci', utils.INVALID_ID
    INVALID_REMOTE_CI_ERROR = 'remoteci', schemas.INVALID_REMOTE_CI

    schema = schemas.job
    data = dict([utils.NAME, JOB_DEFINITION, REMOTE_CI, TEAM])

    def test_post_extra_data(self):
        super(TestJob, self).test_post(self.data, self.data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name', 'jobdefinition', 'remoteci',
                                       'team')
        super(TestJob, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids = dict([utils.INVALID_NAME, self.INVALID_JOB_DEFINITION,
                         self.INVALID_REMOTE_CI, self.INVALID_TEAM])
        errors = dict([utils.INVALID_NAME_ERROR, self.INVALID_REMOTE_CI_ERROR,
                       self.INVALID_JOB_DEFINITION_ERROR,
                       self.INVALID_TEAM_ERROR])

        super(TestJob, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        super(TestJob, self).test_post(self.data, self.data)

    def test_put_extra_data(self):
        super(TestJob, self).test_put_extra_data(self.data)

    def test_put_invalid_data(self):
        invalids = dict([utils.INVALID_NAME, self.INVALID_JOB_DEFINITION,
                         self.INVALID_REMOTE_CI, self.INVALID_TEAM])
        errors = dict([utils.INVALID_NAME_ERROR, self.INVALID_REMOTE_CI_ERROR,
                       self.INVALID_JOB_DEFINITION_ERROR,
                       self.INVALID_TEAM_ERROR])

        super(TestJob, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        super(TestJob, self).test_put(self.data, self.data)


class TestJobState(utils.SchemaTesting):
    JOB = 'job', utils.ID[1]
    INVALID_JOB = 'job', utils.INVALID_ID
    INVALID_JOB_ERROR = 'job', schemas.INVALID_JOB

    TEAM = 'team', utils.ID[1]
    INVALID_TEAM = 'team', utils.INVALID_ID
    INVALID_TEAM_ERROR = 'team', schemas.INVALID_TEAM

    schema = schemas.jobstate
    data = dict([utils.NAME, utils.STATUS, JOB, TEAM])

    def test_post_extra_data(self):
        data = utils.dict_merge(self.data, {'comment': 'some comment'})
        super(TestJobState, self).test_post_extra_data(data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name', 'status', 'team', 'job')
        super(TestJobState, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        status_invalid, status_error = utils.generate_invalid_string('status')

        invalids = dict([utils.INVALID_NAME, self.INVALID_JOB,
                         self.INVALID_TEAM, status_invalid])
        errors = dict([utils.INVALID_NAME_ERROR, self.INVALID_JOB_ERROR,
                       self.INVALID_TEAM_ERROR, status_error])

        super(TestJobState, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        super(TestJobState, self).test_post(self.data, self.data)

    def test_put_extra_data(self):
        super(TestJobState, self).test_put_extra_data(self.data)

    def test_put_invalid_data(self):
        status_invalid, status_error = utils.generate_invalid_string('status')

        invalids = dict([utils.INVALID_NAME, self.INVALID_JOB,
                         self.INVALID_TEAM, status_invalid])
        errors = dict([utils.INVALID_NAME_ERROR, self.INVALID_JOB_ERROR,
                       self.INVALID_TEAM_ERROR, status_error])

        super(TestJobState, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        super(TestJobState, self).test_put(self.data, self.data)


class TestFile(utils.SchemaTesting):
    JOB_STATE = 'jobstate', utils.ID[1]
    INVALID_JOB_STATE = 'jobstate', utils.INVALID_ID
    INVALID_JOB_STATE_ERROR = 'jobstate', schemas.INVALID_JOB_STATE

    TEAM = 'team', utils.ID[1]
    INVALID_TEAM = 'team', utils.INVALID_ID
    INVALID_TEAM_ERROR = 'team', schemas.INVALID_TEAM

    schema = schemas.file
    data = dict([utils.NAME, utils.CONTENT, JOB_STATE, TEAM])

    def test_post_extra_data(self):
        data = utils.dict_merge(self.data, {'mime': 'mime', 'md5': 'md5'})
        super(TestFile, self).test_post_extra_data(data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name', 'content', 'team', 'jobstate')
        super(TestFile, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids = []
        errors = []

        for field in ['content', 'md5', 'mime']:
            invalid, error = utils.generate_invalid_string(field)
            invalids.append(invalid)
            errors.append(error)

        invalids = dict([utils.INVALID_NAME, self.INVALID_JOB_STATE,
                         self.INVALID_TEAM] + invalids)
        errors = dict([utils.INVALID_NAME_ERROR, self.INVALID_JOB_STATE_ERROR,
                       self.INVALID_TEAM_ERROR] + errors)

        super(TestFile, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        super(TestFile, self).test_post(self.data, self.data)

    def test_put_extra_data(self):
        super(TestFile, self).test_put_extra_data(self.data)

    def test_put_invalid_data(self):
        invalids = []
        errors = []

        for field in ['content', 'md5', 'mime']:
            invalid, error = utils.generate_invalid_string(field)
            invalids.append(invalid)
            errors.append(error)

        invalids = dict([utils.INVALID_NAME, self.INVALID_JOB_STATE,
                         self.INVALID_TEAM] + invalids)
        errors = dict([utils.INVALID_NAME_ERROR, self.INVALID_JOB_STATE_ERROR,
                       self.INVALID_TEAM_ERROR] + errors)

        super(TestFile, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        super(TestFile, self).test_put(self.data, self.data)
