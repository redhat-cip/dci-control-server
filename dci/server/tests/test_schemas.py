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

import copy
import datetime
import dci.server.common.exceptions as exceptions
import dci.server.common.schemas as schemas
import flask
import hashlib
import pytest
import six
import uuid
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
            'errors': {'id': ['required key not provided']}
        }
    }


def generate_data(extra=None):
    data = {
        'id': uuid.uuid4(),
        'etag': hashlib.md5().hexdigest(),
        'name': 'foo',
        'created_at': datetime.datetime.now(),
        'updated_at': datetime.datetime.now()
    }

    data.update(extra or {})
    data_dump = copy.deepcopy(data)

    data_dump['id'] = str(data_dump['id'])
    data_dump['created_at'] = data_dump['created_at'].isoformat()
    data_dump['updated_at'] = data_dump['updated_at'].isoformat()
    return data, data_dump


class SchemaTesting(object):
    schema = None
    post_fields = []
    put_fields = []

    def test_dump(self):
        data, data_dump = generate_data({'extra': 'bar'})
        data_dump.pop('extra')
        assert self.schema(data) == data_dump

    def test_post_extra_data(self):
        _, data = generate_data()

        data_post = {'extra': 'bar'}
        # remove extra keys for comprehension
        for key, value in six.iteritems(data):
            if key in self.post_fields:
                data_post[key] = value

        with pytest.raises(exceptions.APIException) as exc:
            self.schema.post(data_post)

        assert exc.value.payload == {
            'errors': {'extra': ['extra keys not allowed']}
        }

    def test_post_missing_data(self):
        errors = {}
        # retrieve all post fields
        for field in self.post_fields:
            errors[str(field)] = ['required key not provided']

        with pytest.raises(exceptions.APIException) as exc:
            self.schema.post({})

        assert exc.value.payload == {'errors': errors}

    def test_post_invalid_data(self):
        """Too complicated to handle this generically,
        let the user implement the test
        """
        raise NotImplementedError

    def test_post(self):
        expected_data_post, data_post = {}, {}
        expected_data, data = generate_data()

        for key, value in six.iteritems(data):
            if key in self.post_fields:
                data_post[key] = value

        for key, value in six.iteritems(expected_data):
            if key in self.post_fields:
                expected_data_post[key] = value

        assert self.schema.post(data_post) == expected_data_post

    def test_put_extra_data(self):
        _, data = generate_data()

        data_put = {'extra': 'bar'}
        # remove extra keys for comprehension
        for key, value in six.iteritems(data):
            if key in self.put_fields:
                data_put[key] = value

        with pytest.raises(exceptions.APIException) as exc:
            self.schema.put(data_put)

        assert exc.value.payload == {
            'errors': {'extra': ['extra keys not allowed']}
        }

    def test_put_missing_data(self):
        errors = {}
        # retrieve all put fields
        for field in self.put_fields:
            errors[str(field)] = ['required key not provided']

        with pytest.raises(exceptions.APIException) as exc:
            self.schema.put({})

        assert exc.value.payload == {'errors': errors}

    def test_put_invalid_data(self):
        """Too complicated to handle this generically,
        let the user implement the test
        """
        raise NotImplementedError

    def test_put(self):
        expected_data_put, data_put = {}, {}
        expected_data, data = generate_data()

        for key, value in six.iteritems(data):
            if key in self.put_fields or key in self.post_fields:
                data_put[key] = value

        for key, value in six.iteritems(expected_data):
            if key in self.put_fields or key in self.post_fields:
                expected_data_put[key] = value

        assert self.schema.put(data_put) == expected_data_put


class BaseSchemaTesting(SchemaTesting):
    post_fields = ['name']
    put_fields = ['id', 'etag']

    def test_post_invalid_data(self):
        pass

    def test_put_invalid_data(self):
        with pytest.raises(exceptions.APIException) as exc:
            self.schema.put({
                'id': 'invalid_uuid',
                'etag': 'invalid_etag'
            })
        assert exc.value.payload == {'errors': {
            'id': ['not a valid uuid'],
            'etag': ['not a valid etag']
        }}


class TestComponentType(BaseSchemaTesting):
    schema = schemas.component_type


class TestTeam(BaseSchemaTesting):
    schema = schemas.team


class TestRole(BaseSchemaTesting):
    schema = schemas.role
