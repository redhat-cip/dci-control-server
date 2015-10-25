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
        def format_error(error):
            path = error.path.pop()
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
    'id': v.Coerce(six.text_type),
    'etag': six.string_types[0],
    'name': six.text_type,
    'created_at': DatetimeFormat(),
    'updated_at': DatetimeFormat()
}

base_load = {
    'id': v.Coerce(uuid.UUID, 'not a valid uuid'),
    'etag': v.All(six.string_types[0], v.Match(ETAG, 'not a valid etag')),
    'name': six.text_type
}


def schema_factory(schema, schema_load):
    schema_post = {}
    schema_put = {}

    for key, value in six.iteritems(schema_load):
        if key in ['id', 'etag']:
            continue
        schema_post[v.Required(key)] = value

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
