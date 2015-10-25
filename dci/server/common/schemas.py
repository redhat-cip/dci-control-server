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

import dci.server.common.exceptions as exceptions
import dci.server.utils as utils
import re
import six
import uuid
import voluptuous as v

ETAG = re.compile('^[a-zA-Z0-9]+$')


class Schema(v.Schema):
    """Override voluptuous schema to return our own error"""
    def __call__(self, data):

        def format_error_message(error):
            # Replace the error message for dict by json
            if error.error_message == 'expected dict':
                error.error_message = 'not a valid json'
            if error.error_message == 'expected str':
                error.error_message = 'not a valid string'

        def format_error(error):
            path = error.path.pop()
            format_error_message(error)
            err = format_error(error) if error.path else [error.error_message]
            return {str(path): err}

        try:
            return super(Schema, self).__call__(data)
        except v.MultipleInvalid as exc:
            errors = {}
            for error in exc.errors:
                errors = utils.dict_merge(errors, format_error(error))
            raise exceptions.APIException('Request malformed',
                                          {'errors': errors})


def DatetimeFormat(format=None):
    return lambda v: v.strftime(format) if format else v.isoformat()


base = {
    'id': v.Coerce(str),
    'etag': str,
    'name': str,
    'created_at': DatetimeFormat(),
    'updated_at': DatetimeFormat()
}

base_load = {
    'id': v.Coerce(uuid.UUID, 'not a valid uuid'),
    'etag': v.All(str, v.Match(ETAG, 'not a valid etag')),
    'name': str
}


test = utils.dict_merge(base, {v.Optional('data', default={}): dict})
test_load = utils.dict_merge(base_load, {v.Optional('data', default={}): dict})


def schema_factory(schema, schema_load):
    schema_post = {}
    schema_put = {}

    for key, value in six.iteritems(schema_load):
        if key in ['id', 'etag']:
            continue

        if not isinstance(key, v.Marker):
            key = v.Required(key)

        schema_post[key] = value

    for key, value in six.iteritems(schema_load):
        if key in ['id', 'etag']:
            schema_put[v.Required(key)] = value
        else:
            schema_put[key] = value

    schema = Schema(schema, extra=v.REMOVE_EXTRA)
    schema.post = Schema(schema_post)
    schema.put = Schema(schema_put)

    return schema

component_type = schema_factory(base, base_load)
team = schema_factory(base, base_load)
role = schema_factory(base, base_load)
test = schema_factory(test, test_load)
