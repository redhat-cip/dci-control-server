# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Red Hat, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from __future__ import unicode_literals

import dci.common.exceptions as exceptions
import dci.common.schemas as schemas
import dci.common.utils as utils
import pytest
import six

# convenient alias
dict_merge = utils.dict_merge
text_type = six.text_type()

ID = 'id', text_type

NAME = 'name', text_type
TYPE = 'type', text_type
ETAG = 'etag', text_type
DATA = 'data', {'foo': 'bar'}
PASSWORD = 'password', text_type
ROLE = 'role', 'admin'
URL = 'url', 'http://valid.url'
STATUS = 'status', text_type
CONTENT = 'content', text_type

INVALID_NAME = 'name', None
INVALID_NAME_ERROR = 'name', schemas.INVALID_STRING

INVALID_ID = 'id', None
INVALID_ID_ERROR = 'id', schemas.INVALID_UUID

INVALID_DATA = 'data', []
INVALID_DATA_ERROR = 'data', schemas.INVALID_JSON

INVALID_PASSWORD = 'password', None
INVALID_PASSWORD_ERROR = 'password', schemas.INVALID_STRING

INVALID_ROLE = 'role', text_type
INVALID_ROLE_ERROR = 'role', schemas.INVALID_ROLE

INVALID_URL = 'url', text_type
INVALID_URL_ERROR = 'url', schemas.INVALID_URL

TEAM = 'team_id', ID[1]
INVALID_TEAM = 'team_id', INVALID_ID
INVALID_TEAM_ERROR = 'team_id', schemas.INVALID_TEAM

TEST = 'test_id', ID[1]
INVALID_TEST = 'test_id', INVALID_ID
INVALID_TEST_ERROR = 'test_id', schemas.INVALID_TEST

TOPIC = 'topic_id', ID[1]
INVALID_TOPIC = 'topic_id', INVALID_ID
INVALID_TOPIC_ERROR = 'topic_id', schemas.INVALID_TOPIC

INVALID_PRIORITY_ERROR = 'priority', schemas.INVALID_PRIORITY

JOB_DEFINITION = 'jobdefinition_id', ID[1]
INVALID_JOB_DEFINITION = 'jobdefinition_id', INVALID_ID
INVALID_JOB_DEFINITION_ERROR = ('jobdefinition_id',
                                schemas.INVALID_JOB_DEFINITION)

REMOTE_CI = 'remoteci_id', ID[1]
INVALID_REMOTE_CI = 'remoteci_id', INVALID_ID
INVALID_REMOTE_CI_ERROR = 'remoteci_id', schemas.INVALID_REMOTE_CI
ACTIVE = 'active', True

JOB = 'job_id', ID[1]
INVALID_JOB = 'job_id', INVALID_ID
INVALID_JOB_ERROR = 'job_id', schemas.INVALID_JOB

JOB_STATE = 'jobstate_id', ID[1]
INVALID_JOB_STATE = 'jobstate_id', INVALID_ID
INVALID_JOB_STATE_ERROR = 'jobstate_id', schemas.INVALID_JOB_STATE


def generate_errors(*fields):
    return dict([(field, schemas.INVALID_REQUIRED) for field in fields])


def generate_invalid_string(field):
    return (field, None), (field, schemas.INVALID_STRING)


def invalid_args(data, errors):
    with pytest.raises(exceptions.DCIException) as exc:
        schemas.args(data)

    assert exc.value.payload == {'errors': errors}


class SchemaTesting(object):
    schema = None

    def test_none(self):
        with pytest.raises(exceptions.DCIException) as exc:
            self.schema.post(None)
        assert exc.value.payload == {'errors': schemas.INVALID_OBJECT}

        with pytest.raises(exceptions.DCIException) as exc:
            self.schema.put(None)
        assert exc.value.payload == {'errors': schemas.INVALID_OBJECT}

    def test_post_extra_data(self, data):
        data_post = {'extra': 'bar'}
        data_post.update(data)
        with pytest.raises(exceptions.DCIException) as exc:
            self.schema.post(data_post)

        assert exc.value.payload == {
            'errors': {'extra': 'extra keys not allowed'}
        }

    def test_post_missing_data(self, errors):
        with pytest.raises(exceptions.DCIException) as exc:
            self.schema.post({})

        assert exc.value.payload == {'errors': errors}

    def test_post_invalid_data(self, data, errors):
        with pytest.raises(exceptions.DCIException) as exc:
            self.schema.post(data)

        assert exc.value.payload == {'errors': errors}

    def test_post(self, data, expected_data):
        assert self.schema.post(data) == expected_data

    def test_put_extra_data(self, data):
        data_put = {'extra': 'bar'}
        data_put.update(data)

        with pytest.raises(exceptions.DCIException) as exc:
            self.schema.put(data_put)

        assert exc.value.payload == {
            'errors': {'extra': 'extra keys not allowed'}
        }

    def test_put_invalid_data(self, data, errors):
        with pytest.raises(exceptions.DCIException) as exc:
            self.schema.put(data)
        assert exc.value.payload == {'errors': errors}

    def test_put(self, data, expected_data):
        assert self.schema.put(data) == expected_data
