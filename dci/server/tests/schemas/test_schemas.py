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
    schema = schemas.componenttype


class TestTeam(BaseSchemaTesting):
    schema = schemas.team


class TestRole(BaseSchemaTesting):
    schema = schemas.role


class TestTest(utils.SchemaTesting):
    schema = schemas.test
    data = dict([utils.NAME])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = dict([utils.INVALID_NAME, utils.INVALID_DATA])
        errors = dict([utils.INVALID_NAME_ERROR, utils.INVALID_DATA_ERROR])
        return invalids, errors

    def test_post_extra_data(self):
        data = data_expected = utils.dict_merge(
            self.data, {'data': {'foo': {'bar': 'baz'}}}
        )
        super(TestTest, self).test_post(data, data_expected)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name')
        super(TestTest, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestTest.generate_invalids_and_errors()
        super(TestTest, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        # add default values to voluptuous output
        data_expected = utils.dict_merge(self.data, {'data': {}})
        super(TestTest, self).test_post(self.data, data_expected)

    def test_put_extra_data(self):
        invalids, errors = TestTest.generate_invalids_and_errors()
        super(TestTest, self).test_put_extra_data(self.data)

    def test_put_invalid_data(self):
        invalids, errors = TestTest.generate_invalids_and_errors()
        super(TestTest, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        # add default values to voluptuous output
        data_expected = utils.dict_merge(self.data, {'data': {}})
        super(TestTest, self).test_put(self.data, data_expected)


class TestUser(utils.SchemaTesting):
    schema = schemas.user
    data = dict([utils.NAME, utils.PASSWORD, utils.TEAM, utils.ROLE])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = dict([utils.INVALID_NAME, utils.INVALID_PASSWORD,
                         utils.INVALID_TEAM])
        errors = dict([utils.INVALID_NAME_ERROR, utils.INVALID_TEAM_ERROR,
                       utils.INVALID_PASSWORD_ERROR])
        return invalids, errors

    def test_post_extra_data(self):
        super(TestUser, self).test_post_extra_data(self.data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name', 'password', 'team_id')
        super(TestUser, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestUser.generate_invalids_and_errors()
        super(TestUser, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        super(TestUser, self).test_post(self.data, self.data)

    def test_put_extra_data(self):
        super(TestUser, self).test_put_extra_data(self.data)

    def test_put_invalid_data(self):
        invalids, errors = TestUser.generate_invalids_and_errors()
        super(TestUser, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        super(TestUser, self).test_put(self.data, self.data)


class TestComponent(utils.SchemaTesting):
    schema = schemas.component
    data = dict([utils.NAME, utils.COMPONENTTYPE])

    @staticmethod
    def generate_optionals():
        return dict([('sha', None), ('title', None), ('message', None),
                     ('git', None), ('ref', None), ('url', None),
                     ('data', {}), ('canonical_project_name', None)])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = []
        errors = []
        for field in ['sha', 'title', 'message', 'git', 'ref',
                      'canonical_project_name']:
            invalid, error = utils.generate_invalid_string(field)
            invalids.append(invalid)
            errors.append(error)

        invalids = dict([utils.INVALID_NAME, utils.INVALID_COMPONENTTYPE,
                         utils.INVALID_DATA] + invalids)
        errors = dict([utils.INVALID_NAME_ERROR,
                       utils.INVALID_COMPONENTTYPE_ERROR,
                       utils.INVALID_DATA_ERROR] + errors)

        return invalids, errors

    def test_post_extra_data(self):
        super(TestComponent, self).test_post_extra_data(self.data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name', 'componenttype_id')
        super(TestComponent, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestComponent.generate_invalids_and_errors()
        super(TestComponent, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        # add default values to voluptuous output
        data_expected = utils.dict_merge(self.data,
                                         TestComponent.generate_optionals())
        super(TestComponent, self).test_post(self.data, data_expected)

    def test_put_extra_data(self):
        super(TestComponent, self).test_put_extra_data(self.data)

    def test_put_invalid_data(self):
        invalids, errors = TestComponent.generate_invalids_and_errors()
        super(TestComponent, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        # add default values to voluptuous output
        data_expected = utils.dict_merge(self.data,
                                         TestComponent.generate_optionals())
        super(TestComponent, self).test_put(self.data, data_expected)


class TestJobDefinition(utils.SchemaTesting):
    schema = schemas.jobdefinition
    data = dict([utils.NAME, utils.TEST])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = dict([utils.INVALID_NAME, utils.INVALID_TEST,
                         ('priority', -1)])
        errors = dict([utils.INVALID_NAME_ERROR, utils.INVALID_TEST_ERROR,
                       utils.INVALID_PRIORITY_ERROR])
        return invalids, errors

    def test_post_extra_data(self):
        data = utils.dict_merge(self.data, {'priority': 10})
        super(TestJobDefinition, self).test_post_extra_data(data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name', 'test_id')
        super(TestJobDefinition, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestJobDefinition.generate_invalids_and_errors()
        super(TestJobDefinition, self).test_post_invalid_data(invalids, errors)
        invalids['priority'] = 1001
        super(TestJobDefinition, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        # add default values to voluptuous output
        data_expected = utils.dict_merge(self.data, {'priority': 0})
        super(TestJobDefinition, self).test_post(self.data, data_expected)

    def test_put_extra_data(self):
        super(TestJobDefinition, self).test_put_extra_data(self.data)

    def test_put_invalid_data(self):
        invalids, errors = TestJobDefinition.generate_invalids_and_errors()

        super(TestJobDefinition, self).test_put_invalid_data(invalids, errors)
        invalids['priority'] = 1001
        super(TestJobDefinition, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        # add default values to voluptuous output
        data_expected = utils.dict_merge(self.data, {'priority': 0})
        super(TestJobDefinition, self).test_put(self.data, data_expected)


class TestRemoteCI(utils.SchemaTesting):
    schema = schemas.remoteci
    data = dict([utils.NAME, utils.TEAM])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = dict([utils.INVALID_NAME, utils.INVALID_TEAM])
        errors = dict([utils.INVALID_NAME_ERROR, utils.INVALID_TEAM_ERROR])
        return invalids, errors

    def test_post_extra_data(self):
        data = data_expected = utils.dict_merge(
            self.data, {'data': {'foo': {'bar': 'baz'}}}
        )
        super(TestRemoteCI, self).test_post(data, data_expected)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name', 'team_id')
        super(TestRemoteCI, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestRemoteCI.generate_invalids_and_errors()
        super(TestRemoteCI, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        # add default values to voluptuous output
        data_expected = utils.dict_merge(self.data, {'data': {}})
        super(TestRemoteCI, self).test_post(self.data, data_expected)

    def test_put_extra_data(self):
        super(TestRemoteCI, self).test_put_extra_data(self.data)

    def test_put_invalid_data(self):
        invalids, errors = TestRemoteCI.generate_invalids_and_errors()
        super(TestRemoteCI, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        # add default values to voluptuous output
        data_expected = utils.dict_merge(self.data, {'data': {}})
        super(TestRemoteCI, self).test_put(self.data, data_expected)


class TestJob(utils.SchemaTesting):
    schema = schemas.job
    data = dict([utils.JOB_DEFINITION, utils.REMOTE_CI, utils.TEAM])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = dict([utils.INVALID_JOB_DEFINITION,
                         utils.INVALID_REMOTE_CI, utils.INVALID_TEAM])
        errors = dict([utils.INVALID_REMOTE_CI_ERROR,
                       utils.INVALID_JOB_DEFINITION_ERROR,
                       utils.INVALID_TEAM_ERROR])
        return invalids, errors

    def test_post_extra_data(self):
        super(TestJob, self).test_post(self.data, self.data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('jobdefinition_id',
                                       'remoteci_id', 'team_id')
        super(TestJob, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestJob.generate_invalids_and_errors()
        super(TestJob, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        super(TestJob, self).test_post(self.data, self.data)

    def test_put_extra_data(self):
        super(TestJob, self).test_put_extra_data(self.data)

    def test_put_invalid_data(self):
        invalids, errors = TestJob.generate_invalids_and_errors()
        super(TestJob, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        super(TestJob, self).test_put(self.data, self.data)


class TestJobSchedule(utils.SchemaTesting):
    schema = schemas.job_schedule
    data = dict([utils.REMOTE_CI])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = dict([utils.INVALID_REMOTE_CI])
        errors = dict([utils.INVALID_REMOTE_CI_ERROR])
        return invalids, errors

    def test_post_extra_data(self):
        super(TestJobSchedule, self).test_post(self.data, self.data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('remoteci_id')
        super(TestJobSchedule, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestJobSchedule.generate_invalids_and_errors()
        super(TestJobSchedule, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        super(TestJobSchedule, self).test_post(self.data, self.data)

    def test_put_extra_data(self):
        pass

    def test_put_invalid_data(self):
        pass

    def test_put(self):
        pass


class TestJobState(utils.SchemaTesting):
    schema = schemas.jobstate
    data = dict([utils.STATUS, utils.JOB, utils.TEAM])

    @staticmethod
    def generate_invalids_and_errors():
        status_invalid, status_error = utils.generate_invalid_string('status')

        invalids = dict([utils.INVALID_JOB,
                         utils.INVALID_TEAM, status_invalid])
        errors = dict([utils.INVALID_JOB_ERROR,
                       utils.INVALID_TEAM_ERROR, status_error])
        return invalids, errors

    def test_post_extra_data(self):
        data = utils.dict_merge(self.data, {'comment': 'some comment'})
        super(TestJobState, self).test_post_extra_data(data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('status', 'team_id', 'job_id')
        super(TestJobState, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestJobState.generate_invalids_and_errors()
        super(TestJobState, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        super(TestJobState, self).test_post(self.data, self.data)

    def test_put_extra_data(self):
        super(TestJobState, self).test_put_extra_data(self.data)

    def test_put_invalid_data(self):
        invalids, errors = TestJobState.generate_invalids_and_errors()
        super(TestJobState, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        super(TestJobState, self).test_put(self.data, self.data)


class TestFile(utils.SchemaTesting):
    schema = schemas.file
    data = dict([utils.NAME, utils.CONTENT, utils.JOB_STATE, utils.TEAM])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = []
        errors = []

        for field in ['content', 'md5', 'mime']:
            invalid, error = utils.generate_invalid_string(field)
            invalids.append(invalid)
            errors.append(error)

        invalids = dict([utils.INVALID_NAME, utils.INVALID_JOB_STATE,
                         utils.INVALID_TEAM] + invalids)
        errors = dict([utils.INVALID_NAME_ERROR, utils.INVALID_JOB_STATE_ERROR,
                       utils.INVALID_TEAM_ERROR] + errors)
        return invalids, errors

    def test_post_extra_data(self):
        data = utils.dict_merge(self.data, {'mime': 'mime', 'md5': 'md5'})
        super(TestFile, self).test_post_extra_data(data)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name', 'content', 'team_id',
                                       'jobstate_id')
        super(TestFile, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestFile.generate_invalids_and_errors()
        super(TestFile, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        # add default values to voluptuous output
        data_expected = utils.dict_merge(self.data,
                                         {'mime': None, 'md5': None})
        super(TestFile, self).test_post(self.data, data_expected)

    def test_put_extra_data(self):
        super(TestFile, self).test_put_extra_data(self.data)

    def test_put_invalid_data(self):
        invalids, errors = TestFile.generate_invalids_and_errors()
        super(TestFile, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        # add default values to voluptuous output
        data_expected = utils.dict_merge(self.data,
                                         {'mime': None, 'md5': None})
        super(TestFile, self).test_put(self.data, data_expected)
