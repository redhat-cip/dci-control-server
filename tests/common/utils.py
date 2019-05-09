# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Red Hat, Inc
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
import pytest
import six
import uuid

# convenient alias
text_type = six.text_type()

ID = 'id', uuid.uuid4()

NAME = 'name', text_type
FULLNAME = 'fullname', text_type
TYPE = 'type', text_type
DESCRIPTION = 'description', text_type
LABEL = 'label', text_type
TIMEZONE = 'timezone', 'Europe/Paris'
ETAG = 'etag', text_type
DATA = 'data', {'foo': 'bar'}
PASSWORD = 'password', text_type
URL = 'url', 'http://valid.url'
STATUS = 'status', text_type
STATE = 'state', 'active'
COMMENT = 'comment', text_type
CONTENT = 'content', text_type
LABEL = 'label', text_type
NEXT_TOPIC_ID = 'next_topic_id', uuid.uuid4()
COUNTRY = 'country', text_type
EMAIL = 'email', 'foo@bar.org'
VALUE = 'value', text_type
PUBLIC = 'public', False
EXTERNAL = 'external', True
PREVIOUS_JOB_ID = 'previous_job_id', uuid.uuid4()
UPDATE_PREVIOUS_JOB_ID = 'update_previous_job_id', uuid.uuid4()
EXPORT_CONTROL = 'export_control', False
TYPE = 'type', text_type

INVALID_NAME = 'name', None
INVALID_NAME_ERROR = 'name', schemas.INVALID_STRING

INVALID_FULLNAME = 'fullname', None
INVALID_FULLNAME_ERROR = 'fullname', schemas.INVALID_STRING

INVALID_ID = 'id', None
INVALID_ID_ERROR = 'id', schemas.INVALID_UUID

INVALID_DATA = 'data', []
INVALID_DATA_ERROR = 'data', schemas.INVALID_JSON

INVALID_PASSWORD = 'password', None
INVALID_PASSWORD_ERROR = 'password', schemas.INVALID_STRING

INVALID_EMAIL = 'email', 'lal@lolo'
INVALID_EMAIL_ERROR = 'email', schemas.INVALID_EMAIL

INVALID_URL = 'url', text_type
INVALID_URL_ERROR = 'url', schemas.INVALID_URL

INVALID_TIMEZONE = 'timezone', 'NonContinent/NonCity'
INVALID_TIMEZONE_ERROR = 'timezone', schemas.INVALID_TIMEZONE

PARENT = 'parent_id', ID[1]
INVALID_PARENT = 'parent_id', INVALID_ID
INVALID_PARENT_ERROR = 'parent_id', schemas.INVALID_TEAM

TEAM = 'team_id', ID[1]
INVALID_TEAM = 'team_id', INVALID_ID
INVALID_TEAM_ERROR = 'team_id', schemas.INVALID_TEAM

TEST = 'test_id', ID[1]
INVALID_TEST = 'test_id', INVALID_ID
INVALID_TEST_ERROR = 'test_id', schemas.INVALID_TEST

TOPIC = 'topic_id', ID[1]
INVALID_TOPIC = 'topic_id', INVALID_ID
INVALID_TOPIC_ERROR = 'topic_id', schemas.INVALID_TOPIC

TOPIC_SECONDARY = 'topic_id_secondary', ID[1]
INVALID_TOPIC_SECONDARY = 'topic_id_secondary', INVALID_ID
INVALID_TOPIC_SECONDARY_ERROR = 'topic_id_secondary', schemas.INVALID_TOPIC

PRODUCT = 'product_id', ID[1]
INVALID_PRODUCT = 'product_id', INVALID_ID
INVALID_PRODUCT_ERROR = 'product_id', schemas.INVALID_PRODUCT

REMOTE_CI = 'remoteci_id', ID[1]
INVALID_REMOTE_CI = 'remoteci_id', INVALID_ID
INVALID_REMOTE_CI_ERROR = 'remoteci_id', schemas.INVALID_REMOTE_CI

JOB = 'job_id', ID[1]
INVALID_JOB = 'job_id', INVALID_ID
INVALID_JOB_ERROR = 'job_id', schemas.INVALID_JOB

JOB_STATE = 'jobstate_id', ID[1]
INVALID_JOB_STATE = 'jobstate_id', INVALID_ID
INVALID_JOB_STATE_ERROR = 'jobstate_id', schemas.INVALID_JOB_STATE

INVALID_COMMENT = 'comment', None
INVALID_COMMENT_ERROR = 'comment', schemas.INVALID_STRING

COMPONENTS = 'components', []
INVALID_COMPONENTS = 'components', list
INVALID_COMPONENTS_ERROR = 'components', schemas.INVALID_LIST

COMPONENTS_IDS = 'components_ids', []
INVALID_COMPONENTS_IDS = 'components_ids', list
INVALID_COMPONENTS_IDS_ERROR = 'components_ids', schemas.INVALID_LIST

INVALID_VALUE = 'value', None
INVALID_VALUE_ERROR = 'value', schemas.INVALID_STRING


INVALID_TYPE = 'type', None
INVALID_TYPE_ERROR = 'type', schemas.INVALID_TYPE


def generate_errors(*fields):
    return dict([(field, schemas.INVALID_REQUIRED) for field in fields])


def generate_invalid_string(field):
    return (field, None), (field, schemas.INVALID_STRING)


def generate_invalid_url(field):
    return (field, None), (field, schemas.INVALID_URL)


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

    def test_put_invalid_data(self, data, errors):
        with pytest.raises(exceptions.DCIException) as exc:
            self.schema.put(data)
            assert exc.value.payload == {'errors': errors}

    def test_put(self, data, expected_data):
        assert self.schema.put(data) == expected_data
