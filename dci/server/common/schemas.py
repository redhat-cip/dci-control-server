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

import dci.server.common.exceptions as exceptions
import dci.server.utils as utils
import six
import voluptuous as v


INVALID_UUID = 'not a valid uuid'
INVALID_STRING = 'not a valid string'
INVALID_ETAG = 'not a valid etag'

INVALID_REQUIRED = 'required key not provided'

UUID_FIELD = v.All(six.text_type, msg=INVALID_UUID)
ETAG_FIELD = v.Any(None, six.text_type, int, msg=INVALID_ETAG)


class Schema(v.Schema):
    """Override voluptuous schema to return our own error"""

    error_messages = {
        'expected unicode': INVALID_STRING,
        'expected str': INVALID_STRING,
    }

    def __call__(self, data):
        def format_error(error):
            path = error.path.pop()
            msg = error.error_message
            error.error_message = self.error_messages.get(msg, msg)

            err = format_error(error) if error.path else [error.error_message]
            return {six.text_type(path): err}

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
        if key == 'etag':
            schema_put[v.Required(key)] = value
        else:
            schema_put[key] = value

    schema = Schema(schema, extra=v.REMOVE_EXTRA)
    schema.post = Schema(schema_post)
    schema.put = Schema(schema_put)

    return schema

###############################################################################
#                                                                             #
#                                 Base schemas                                #
#                                                                             #
###############################################################################

base = {
    'id': UUID_FIELD,
    'etag': six.text_type,
    'name': six.text_type,
    'created_at': DatetimeFormat(),
    'updated_at': DatetimeFormat()
}

base_load = {
    'etag': ETAG_FIELD,
    'name': six.text_type
}

component_type = schema_factory(base, base_load)
team = schema_factory(base, base_load)
role = schema_factory(base, base_load)
