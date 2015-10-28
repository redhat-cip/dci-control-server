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

import collections
import dci.server.common.exceptions as exceptions
import dci.server.utils as utils
import six
import voluptuous as v


INVALID_STRING = 'not a valid string'
INVALID_REQUIRED = 'required key not provided'


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
            raise exceptions.DCIException('Request malformed',
                                          {'errors': errors})


DCISchema = collections.namedtuple('DCISchema', ['post', 'put'])


def schema_factory(schema):
    schema_post = {}

    for key, value in six.iteritems(schema):
        if not isinstance(key, v.Marker):
            key = v.Required(key)

        schema_post[key] = value

    return DCISchema(Schema(schema_post), Schema(schema))

###############################################################################
#                                                                             #
#                                 Base schemas                                #
#                                                                             #
###############################################################################

base = {
    'name': six.text_type,
}


component_type = schema_factory(base)
team = schema_factory(base)
role = schema_factory(base)
