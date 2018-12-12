# -*- encoding: utf-8 -*-
#
# Copyright 2018 Red Hat, Inc.
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

from dci.common.exceptions import DCIException
from jsonschema import validators, FormatChecker, Draft4Validator
from jsonschema.exceptions import ValidationError

uuid_pattern = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
email_pattern = "(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"


class Properties(object):
    string = {"type": "string"}
    uuid = {"type": "string", "pattern": uuid_pattern}
    email = {"type": "string", "pattern": email_pattern}
    array = {"type": "array"}
    integer = {"type": "integer"}
    positive_integer = {"type": "integer", "minimum": 0}
    key_value_csv = {"type": "string", "is_key_value_csv": True}


custom_error_messages = {
    uuid_pattern: "is not a valid 'uuid'",
    email_pattern: "is not a valid 'email'",
}


def _is_key_value_csv(validator, value, instance, schema):
    for element in instance.split(","):
        if len(element.split(":")) != 2:
            yield ValidationError("'%s' is not a 'key value csv'" % instance)


all_validators = dict(Draft4Validator.VALIDATORS)
all_validators["is_key_value_csv"] = _is_key_value_csv

DCIValidator = validators.create(
    meta_schema=Draft4Validator.META_SCHEMA, validators=all_validators
)


def _get_error_message(error):
    if error.validator == "pattern":
        property_name = error.path[-1]
        value = error.instance
        msg = custom_error_messages.get(error.validator_value, error.message)
        return "%s: '%s' %s" % (property_name, value, msg)

    if (
        error.validator == "type" and
        error.validator_value in ["string", "array", "integer"]
    ) or (
        error.validator in ["minimum", "is_key_value_csv"]
    ):
        property_name = error.path[-1]
        return "%s: %s" % (property_name, error.message)

    return error.message


def check_json_is_valid(schema, json):
    v = DCIValidator(schema, format_checker=FormatChecker())
    errors = []
    for error in sorted(v.iter_errors(json), key=str):
        errors.append(_get_error_message(error))
    if len(errors):
        raise DCIException("Request malformed", {"errors": errors})


tag_schema = {
    "type": "object",
    "properties": {"name": {"type": "string"}},
    "required": ["name"],
    "additionalProperties": False,
}
