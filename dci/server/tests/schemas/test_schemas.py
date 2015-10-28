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
            'errors': {'id': ['required key not provided']}
        }
    }


class BaseSchemaTesting(utils.SchemaTesting):

    data_post = dict([utils.NAME])
    data_put = dict([utils.NAME, utils.ETAG])

    def test_dump(self):
        data = dict([utils.ID, utils.NAME, utils.ETAG, utils.CREATED_AT,
                     utils.UPDATED_AT, ('extra', 'foo')])

        data_dump = dict([utils.ID, utils.NAME, utils.ETAG,
                          utils.CREATED_AT_DUMP, utils.UPDATED_AT_DUMP])

        super(BaseSchemaTesting, self).test_dump(data, data_dump)

    def test_post_extra_data(self):
        super(BaseSchemaTesting, self).test_post_extra_data(self.data_post)

    def test_post_missing_data(self):
        errors = dict([utils.generate_error('name')])
        super(BaseSchemaTesting, self).test_post_missing_data(errors)

    def test_post_invalid_data(self):
        super(BaseSchemaTesting, self).test_post_invalid_data(
            dict([utils.INVALID_NAME]), dict([utils.INVALID_NAME_ERROR])
        )

    def test_post(self):
        super(BaseSchemaTesting, self).test_post(self.data_post,
                                                 self.data_post)

    def test_put_extra_data(self):
        super(BaseSchemaTesting, self).test_put_extra_data(self.data_put)

    def test_put_missing_data(self):
        errors = dict([utils.generate_error('etag')])
        super(BaseSchemaTesting, self).test_put_missing_data(errors)

    def test_put_invalid_data(self):
        data = dict([utils.INVALID_NAME, utils.INVALID_ETAG])
        errors = dict([utils.INVALID_NAME_ERROR, utils.INVALID_ETAG_ERROR])

        super(BaseSchemaTesting, self).test_put_invalid_data(data, errors)

    def test_put(self):
        super(BaseSchemaTesting, self).test_put(self.data_put, self.data_put)


class TestComponentType(BaseSchemaTesting):
    schema = schemas.component_type


class TestTeam(BaseSchemaTesting):
    schema = schemas.team


class TestRole(BaseSchemaTesting):
    schema = schemas.role
