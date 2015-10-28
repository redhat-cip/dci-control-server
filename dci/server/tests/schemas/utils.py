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

import datetime
import dci.server.common.exceptions as exceptions
import dci.server.common.schemas as schemas
import dci.server.utils as utils
import pytest
import six

# convenient alias
dict_merge = utils.dict_merge

ID = 'id', six.text_type()

NAME = 'name', 'foo'
ETAG = 'etag', six.text_type()
DATA = 'data', {'foo': 'bar'}

UPDATED_AT = 'updated_at', datetime.datetime.now()
UPDATED_AT_DUMP = 'updated_at', UPDATED_AT[1].isoformat()

CREATED_AT = 'created_at', datetime.datetime.now()
CREATED_AT_DUMP = 'created_at', CREATED_AT[1].isoformat()

INVALID_NAME = 'name', None
INVALID_NAME_ERROR = 'name', [schemas.INVALID_STRING]

INVALID_ETAG = 'etag', float()
INVALID_ETAG_ERROR = 'etag', [schemas.INVALID_ETAG]


def generate_error(field):
    return (field, [schemas.INVALID_REQUIRED])


class SchemaTesting(object):
    schema = None

    def test_dump(self, data, expected_data):
        assert self.schema(data) == expected_data

    def test_post_extra_data(self, data):
        data_post = {'extra': 'bar'}
        data_post.update(data)
        with pytest.raises(exceptions.APIException) as exc:
            self.schema.post(data_post)

        assert exc.value.payload == {
            'errors': {'extra': ['extra keys not allowed']}
        }

    def test_post_missing_data(self, errors):
        with pytest.raises(exceptions.APIException) as exc:
            self.schema.post({})

        assert exc.value.payload == {'errors': errors}

    def test_post_invalid_data(self, data, errors):
        with pytest.raises(exceptions.APIException) as exc:
            self.schema.post(data)
        assert exc.value.payload == {'errors': errors}

    def test_post(self, data, expected_data):
        assert self.schema.post(data) == expected_data

    def test_put_extra_data(self, data):
        data_put = {'extra': 'bar'}
        data_put.update(data)

        with pytest.raises(exceptions.APIException) as exc:
            self.schema.put(data_put)

        assert exc.value.payload == {
            'errors': {'extra': ['extra keys not allowed']}
        }

    def test_put_missing_data(self, errors):
        with pytest.raises(exceptions.APIException) as exc:
            self.schema.put({})

        assert exc.value.payload == {'errors': errors}

    def test_put_invalid_data(self, data, errors):
        with pytest.raises(exceptions.APIException) as exc:
            self.schema.put(data)
        assert exc.value.payload == {'errors': errors}

    def test_put(self, data, expected_data):
        assert self.schema.put(data) == expected_data
