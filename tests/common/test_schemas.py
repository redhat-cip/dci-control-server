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
from __future__ import unicode_literals

import dci.common.schemas as schemas
import tests.common.utils as utils

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


def test_dict_merge():
    a = {'jim': 123, 'a': {'b': {'c': {'d': 'bob'}}}, 'rob': 34}
    b = {'tot': {'a': {'b': 'string'}, 'c': [1, 2]}}
    c = {'tot': {'c': [3, 4]}}

    assert schemas.dict_merge(a, b, c) == {
        'a': {'b': {'c': {'d': 'bob'}}},
        'jim': 123,
        'rob': 34,
        'tot': {'a': {'b': 'string'}, 'c': [1, 2, 3, 4]}
    }


class BaseSchemaTesting(utils.SchemaTesting):

    data = dict([utils.NAME])

    def test_post_missing_data(self):
        errors = utils.generate_errors('name')
        super(BaseSchemaTesting, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        super(BaseSchemaTesting, self).test_post_invalid_data(
            dict([utils.INVALID_NAME]), dict([utils.INVALID_NAME_ERROR])
        )

    def test_post(self):
        super(BaseSchemaTesting, self).test_post(self.data, self.data)

    def test_put_invalid_data(self):
        data = dict([utils.INVALID_NAME])
        errors = dict([utils.INVALID_NAME_ERROR])

        super(BaseSchemaTesting, self).test_put_invalid_data(data, errors)

    def test_put(self):
        super(BaseSchemaTesting, self).test_put(self.data, self.data)


class TestComponentType(BaseSchemaTesting):
    schema = schemas.componenttype


class TestTeam(utils.SchemaTesting):
    schema = schemas.team
    data = dict([utils.NAME, utils.COUNTRY, utils.STATE, utils.PARENT,
                 utils.EXTERNAL])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = dict([utils.INVALID_NAME])
        errors = dict([utils.INVALID_NAME_ERROR])
        return invalids, errors

    def test_post_missing_data(self):
        errors = utils.generate_errors('name')
        super(TestTeam, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestTeam.generate_invalids_and_errors()
        super(TestTeam, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        super(TestTeam, self).test_post(self.data, self.data)

    def test_put_invalid_data(self):
        invalids, errors = TestTeam.generate_invalids_and_errors()
        super(TestTeam, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        super(TestTeam, self).test_put(self.data, self.data)


class TestRole(utils.SchemaTesting):
    schema = schemas.role
    data = dict([utils.NAME, utils.STATE, utils.DESCRIPTION])
    data_post = dict([utils.NAME, utils.STATE, utils.DESCRIPTION, utils.LABEL])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = dict([utils.INVALID_NAME])
        errors = dict([utils.INVALID_NAME_ERROR])
        return invalids, errors

    def test_post_missing_data(self):
        errors = utils.generate_errors('name')
        super(TestRole, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestRole.generate_invalids_and_errors()
        super(TestRole, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        super(TestRole, self).test_post(self.data_post, self.data_post)

    def test_put_invalid_data(self):
        invalids, errors = TestRole.generate_invalids_and_errors()
        super(TestRole, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        super(TestRole, self).test_put(self.data, self.data)


class TestTest(utils.SchemaTesting):
    schema = schemas.test
    data = dict([utils.NAME, utils.TEAM, utils.STATE, utils.DATA])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = dict([utils.INVALID_NAME, utils.INVALID_DATA])
        errors = dict([utils.INVALID_NAME_ERROR, utils.INVALID_DATA_ERROR])
        return invalids, errors

    def test_post_missing_data(self):
        errors = utils.generate_errors('name')
        super(TestTest, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestTest.generate_invalids_and_errors()
        super(TestTest, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        # add default values to voluptuous output
        data_expected = schemas.dict_merge(self.data, {'data': {}})
        super(TestTest, self).test_post(self.data, data_expected)

    def test_put_invalid_data(self):
        invalids, errors = TestTest.generate_invalids_and_errors()
        super(TestTest, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        # add default values to voluptuous output
        data_expected = schemas.dict_merge(self.data, {'data': {}})
        super(TestTest, self).test_put(self.data, data_expected)


class TestUser(utils.SchemaTesting):
    schema = schemas.user
    data = dict([utils.NAME, utils.PASSWORD, utils.TEAM, utils.STATE,
                 utils.FULLNAME, utils.EMAIL, utils.TIMEZONE])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = dict([utils.INVALID_NAME, utils.INVALID_PASSWORD,
                         utils.INVALID_TEAM, utils.INVALID_FULLNAME,
                         utils.INVALID_EMAIL, utils.INVALID_TIMEZONE])
        errors = dict([utils.INVALID_NAME_ERROR, utils.INVALID_TEAM_ERROR,
                       utils.INVALID_PASSWORD_ERROR,
                       utils.INVALID_FULLNAME_ERROR,
                       utils.INVALID_EMAIL_ERROR,
                       utils.INVALID_TIMEZONE_ERROR])
        return invalids, errors

    def test_post_missing_data(self):
        errors = utils.generate_errors('name', 'fullname', 'email')
        super(TestUser, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestUser.generate_invalids_and_errors()
        super(TestUser, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        super(TestUser, self).test_post(self.data, self.data)

    def test_put_invalid_data(self):
        invalids, errors = TestUser.generate_invalids_and_errors()
        super(TestUser, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        super(TestUser, self).test_put(self.data, self.data)


class TestComponent(utils.SchemaTesting):
    schema = schemas.component
    data = dict([utils.NAME, utils.TYPE, utils.TOPIC, utils.STATE])

    @staticmethod
    def generate_optionals():
        return dict([('title', None), ('message', None), ('url', None),
                     ('data', {}), ('canonical_project_name', None),
                     ('state', 'active')])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = []
        errors = []

        invalid, error = utils.generate_invalid_string('type')

        invalids = dict([utils.INVALID_NAME, utils.INVALID_DATA,
                         utils.INVALID_TOPIC, invalid])
        errors = dict([utils.INVALID_NAME_ERROR,
                       utils.INVALID_DATA_ERROR,
                       utils.INVALID_TOPIC_ERROR, error])

        return invalids, errors

    def test_post_missing_data(self):
        errors = utils.generate_errors('name', 'type', 'topic_id')
        super(TestComponent, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestComponent.generate_invalids_and_errors()
        super(TestComponent, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        # add default values to voluptuous output
        data_expected = schemas.dict_merge(
            self.data,
            TestComponent.generate_optionals()
        )
        super(TestComponent, self).test_post(self.data, data_expected)

    def test_put_invalid_data(self):
        pass

    def test_put(self):
        pass


class TestRemoteCI(utils.SchemaTesting):
    schema = schemas.remoteci
    data = dict([utils.NAME, utils.TEAM, utils.STATE, utils.PUBLIC])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = dict([utils.INVALID_NAME, utils.INVALID_TEAM])
        errors = dict([utils.INVALID_NAME_ERROR, utils.INVALID_TEAM_ERROR])
        return invalids, errors

    def test_post_missing_data(self):
        errors = utils.generate_errors('name', 'team_id')
        super(TestRemoteCI, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestRemoteCI.generate_invalids_and_errors()
        super(TestRemoteCI, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        # add default values to voluptuous output
        data_expected = schemas.dict_merge(self.data, {'data': {}})
        super(TestRemoteCI, self).test_post(self.data, data_expected)

    def test_put_invalid_data(self):
        invalids, errors = TestRemoteCI.generate_invalids_and_errors()
        super(TestRemoteCI, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        # add default values to voluptuous output
        super(TestRemoteCI, self).test_put(self.data, self.data)


class TestRemoteciRconfigurations(utils.SchemaTesting):
    schema = schemas.rconfiguration
    data = dict([utils.NAME, utils.DATA, utils.TOPIC])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = dict([utils.INVALID_NAME, utils.INVALID_DATA,
                         utils.INVALID_TOPIC])
        errors = dict([utils.INVALID_NAME_ERROR, utils.INVALID_DATA_ERROR,
                       utils.INVALID_TOPIC_ERROR])
        return invalids, errors

    def test_post_missing_data(self):
        errors = utils.generate_errors('topic_id', 'name')
        super(TestRemoteciRconfigurations, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestRemoteciRconfigurations.\
            generate_invalids_and_errors()
        super(TestRemoteciRconfigurations, self).test_post_invalid_data(
            invalids, errors)

    def test_post(self):
        # add default values to voluptuous output
        data_expected = schemas.dict_merge(
            self.data,
            {'data': {}, 'component_types': None}
        )
        super(TestRemoteciRconfigurations, self).test_post(self.data,
                                                           data_expected)

    def test_put_invalid_data(self):
        pass

    def test_put(self):
        pass


class TestJob(utils.SchemaTesting):
    schema = schemas.job
    data = dict([utils.TEAM, utils.COMPONENTS, utils.PREVIOUS_JOB_ID,
                 utils.UPDATE_PREVIOUS_JOB_ID, utils.STATE, utils.TOPIC,
                 utils.RCONFIGURATION, utils.TOPIC_SECONDARY])
    data_put = dict([('status', 'success'), utils.COMMENT])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = dict([utils.INVALID_TEAM,
                         utils.INVALID_COMPONENTS,
                         utils.INVALID_TOPIC,
                         utils.INVALID_RCONFIGURATION,
                         utils.INVALID_TOPIC_SECONDARY])
        errors = dict([utils.INVALID_TEAM_ERROR,
                       utils.INVALID_COMPONENTS_ERROR,
                       utils.INVALID_TOPIC_ERROR,
                       utils.INVALID_RCONFIGURATION_ERROR,
                       utils.INVALID_TOPIC_SECONDARY_ERROR])
        return invalids, errors

    @staticmethod
    def generate_invalids_and_errors_put():
        invalids = dict([utils.INVALID_COMMENT, utils.STATUS])
        errors = dict([utils.INVALID_COMMENT_ERROR,
                       ('status', schemas.INVALID_STATUS_UPDATE)])
        return invalids, errors

    def test_post_missing_data(self):
        errors = utils.generate_errors('components')
        super(TestJob, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestJob.generate_invalids_and_errors()
        super(TestJob, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        # add default values to voluptuous output
        data_expected = schemas.dict_merge(self.data, {'comment': None})
        super(TestJob, self).test_post(self.data, data_expected)

    def test_put_invalid_data(self):
        invalids, errors = TestJob.generate_invalids_and_errors_put()
        super(TestJob, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        super(TestJob, self).test_put(self.data_put, self.data_put)


class TestJobSchedule(utils.SchemaTesting):
    schema = schemas.job_schedule
    data = dict([utils.TOPIC, utils.COMPONENTS_IDS, utils.TOPIC_SECONDARY])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = dict([utils.INVALID_TOPIC,
                         utils.INVALID_COMPONENTS_IDS,
                         utils.INVALID_TOPIC_SECONDARY])
        errors = dict([utils.INVALID_TOPIC_ERROR,
                       utils.INVALID_COMPONENTS_IDS_ERROR,
                       utils.INVALID_TOPIC_SECONDARY_ERROR])
        return invalids, errors

    def test_post_missing_data(self):
        errors = utils.generate_errors('topic_id')
        super(TestJobSchedule, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestJobSchedule.generate_invalids_and_errors()
        super(TestJobSchedule, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        data_expected = schemas.dict_merge(self.data, {'dry_run': False})
        super(TestJobSchedule, self).test_post(self.data, data_expected)

    def test_put_invalid_data(self):
        pass

    def test_put(self):
        pass


class TestIssue(utils.SchemaTesting):
    schema = schemas.issue
    data = dict([utils.URL, utils.TOPIC])

    @staticmethod
    def generate_invalids_and_errors():
        status_invalid, status_error = utils.generate_invalid_url('url')

        invalids = dict([utils.INVALID_URL, status_invalid,
                         utils.INVALID_TOPIC])
        errors = dict([utils.INVALID_URL_ERROR, status_error,
                       utils.INVALID_TOPIC_ERROR])
        return invalids, errors

    def test_post_missing_data(self):
        errors = utils.generate_errors('url')
        super(TestIssue, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestIssue.generate_invalids_and_errors()
        super(TestIssue, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        super(TestIssue, self).test_post(self.data, self.data)

    def test_put_invalid_data(self):
        pass

    def test_put(self):
        pass


class TestMeta(utils.SchemaTesting):
    schema = schemas.meta
    data = dict([utils.NAME, utils.VALUE])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = dict([utils.INVALID_NAME,
                         utils.INVALID_VALUE])
        errors = dict([utils.INVALID_NAME_ERROR,
                       utils.INVALID_VALUE_ERROR])
        return invalids, errors

    def test_post_missing_data(self):
        errors = utils.generate_errors('name')
        super(TestMeta, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestMeta.generate_invalids_and_errors()
        super(TestMeta, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        super(TestMeta, self).test_post(self.data, self.data)

    def test_put_invalid_data(self):
        invalids, errors = TestMeta.generate_invalids_and_errors()
        super(TestMeta, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        # add default values to voluptuous output
        super(TestMeta, self).test_put(self.data, self.data)


class TestJobState(utils.SchemaTesting):
    schema = schemas.jobstate
    data = dict([utils.STATUS, utils.JOB])

    @staticmethod
    def generate_invalids_and_errors():
        status_invalid, status_error = utils.generate_invalid_string('status')

        invalids = dict([utils.INVALID_JOB, status_invalid])
        errors = dict([utils.INVALID_JOB_ERROR, status_error])
        return invalids, errors

    def test_post_missing_data(self):
        errors = utils.generate_errors('status', 'job_id')
        super(TestJobState, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestJobState.generate_invalids_and_errors()
        super(TestJobState, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        pass
        # add default values to voluptuous output
        data_expected = schemas.dict_merge(self.data, {'comment': None})
        super(TestJobState, self).test_post(self.data, data_expected)

    def test_put_invalid_data(self):
        invalids, errors = TestJobState.generate_invalids_and_errors()
        super(TestJobState, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        # add default values to voluptuous output
        data_expected = schemas.dict_merge(self.data, {'comment': None})
        super(TestJobState, self).test_put(self.data, data_expected)


# todo(yassine): this will be re activated when we will verify
# files api call's headers with voluptuous
class LolTestFile(utils.SchemaTesting):
    schema = schemas.file
    data = dict([utils.NAME, utils.CONTENT, utils.JOB_STATE, utils.JOB])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = []
        errors = []

        for field in ['content', 'md5', 'mime']:
            invalid, error = utils.generate_invalid_string(field)
            invalids.append(invalid)
            errors.append(error)

        invalids = dict([utils.INVALID_NAME, utils.INVALID_JOB_STATE] +
                        invalids)
        errors = dict(
            [utils.INVALID_NAME_ERROR, utils.INVALID_JOB_STATE_ERROR] +
            errors
        )
        return invalids, errors

    def test_post_missing_data(self):
        errors = utils.generate_errors('name')
        super(LolTestFile, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = LolTestFile.generate_invalids_and_errors()
        super(LolTestFile, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        # add default values to voluptuous output
        data_expected = schemas.dict_merge(
            self.data,
            {'mime': None, 'md5': None}
        )
        super(LolTestFile, self).test_post(self.data, data_expected)

    def test_put_invalid_data(self):
        invalids, errors = LolTestFile.generate_invalids_and_errors()
        super(LolTestFile, self).test_put_invalid_data(invalids, errors)

    def test_put(self):
        # add default values to voluptuous output
        data_expected = schemas.dict_merge(
            self.data,
            {'mime': None, 'md5': None}
        )
        super(LolTestFile, self).test_put(self.data, data_expected)


class TestTopic(utils.SchemaTesting):
    schema = schemas.topic
    data = dict([utils.NAME, utils.NEXT_TOPIC_ID, utils.STATE,
                 utils.PRODUCT, utils.DATA, utils.EXPORT_CONTROL])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = dict([utils.INVALID_NAME, utils.INVALID_PRODUCT])
        errors = dict([utils.INVALID_NAME_ERROR, utils.INVALID_PRODUCT_ERROR])
        return invalids, errors

    def test_post_missing_data(self):
        errors = utils.generate_errors('name', 'product_id')
        super(TestTopic, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        invalids, errors = TestTopic.generate_invalids_and_errors()
        super(TestTopic, self).test_post_invalid_data(invalids, errors)

    def test_post(self):
        expected = schemas.dict_merge(self.data, {'component_types': []})
        super(TestTopic, self).test_post(self.data, expected)

    def test_put_invalid_data(self):
        pass

    def test_put(self):
        pass


class TestArgs(object):
    data = {
        'limit': '50',
        'offset': '10',
        'sort': 'field_1,field_2',
        'where': 'field_1:value_1,field_2:value_2',
        'embed': 'resource_1,resource_2'
    }

    data_expected = {
        'limit': 50,
        'offset': 10,
        'sort': ['field_1', 'field_2'],
        'where': ['field_1:value_1', 'field_2:value_2'],
        'embed': ['resource_1', 'resource_2']
    }

    def test_extra_args(self):
        extra_data = schemas.dict_merge(self.data, {'foo': 'bar'})
        assert schemas.args(extra_data) == self.data_expected

    def test_default_args(self):
        expected = {
            'limit': None,
            'offset': None,
            'sort': [],
            'where': [],
            'embed': []
        }
        assert schemas.args({}) == expected

    def test_invalid_args(self):
        errors = {'limit': schemas.INVALID_LIMIT,
                  'offset': schemas.INVALID_OFFSET}

        data = {'limit': -1, 'offset': -1}
        utils.invalid_args(data, errors)
        data = {'limit': 'foo', 'offset': 'bar'}
        utils.invalid_args(data, errors)

    def test_args(self):
        assert schemas.args(self.data) == self.data_expected


class TestAnalytics(utils.SchemaTesting):
    schema = schemas.analytic
    data = dict([utils.NAME, utils.URL, utils.TYPE, utils.DATA])

    @staticmethod
    def generate_invalids_and_errors():
        invalids = dict([utils.INVALID_NAME, utils.INVALID_TYPE])
        errors = dict([utils.INVALID_NAME_ERROR, utils.INVALID_TYPE_ERROR])
        return invalids, errors

    def test_post(self):
        data_expected = self.data
        super(TestAnalytics, self).test_post(self.data, data_expected)

    def test_post_invalid_data(self):
        invalids, errors = TestAnalytics.generate_invalids_and_errors()
        super(TestAnalytics, self).test_post_invalid_data(invalids, errors)

    def test_post_missing_data(self):
        errors = utils.generate_errors('name', 'type')
        super(TestAnalytics, self).test_post_missing_data(errors)

    def test_put(self):
        data_expected = self.data
        super(TestAnalytics, self).test_put(self.data, data_expected)

    def test_put_invalid_data(self):
        invalids, errors = TestAnalytics.generate_invalids_and_errors()
        super(TestAnalytics, self).test_put_invalid_data(invalids, errors)
