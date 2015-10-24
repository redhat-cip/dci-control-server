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

import flask
import voluptuous
import dci.server.common.exceptions as exceptions
import dci.server.utils as utils


class Schema(voluptuous.Schema):
    """Override voluptuous schema to return our own error"""
    def __call__(self, data):
        def format_error(error):
            path = error.path.pop()
            return {
                str(path): format_error(error) if error.path
                           else [error.error_message]
            }

        try:
            super(Schema, self).__call__(data)
        except voluptuous.MultipleInvalid as exc:
            errors = {}
            for error in exc.errors:
                errors = utils.dict_merge(errors, format_error(error))
            raise exceptions.APIException('Request malformed',
                                          {'errors': errors})

base = {
    voluptuous.Required('id'): str
}

base_schema = Schema(base)

