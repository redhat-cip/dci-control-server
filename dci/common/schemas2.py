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
from dci.common.args import parse_args
from jsonschema import validators, FormatChecker, Draft4Validator
from jsonschema.exceptions import ValidationError


def allow_none(property):
    result = property.copy()
    result["type"] = [property["type"], "null"]
    return result


def with_default(property, default):
    result = property.copy()
    result["default"] = default
    if default is None:
        return allow_none(result)
    return result


class Properties(object):
    string = {"type": "string"}
    uuid = {
        "type": "string",
        "pattern": "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    }
    email = {"type": "string", "format": "email"}
    url = {"type": "string", "format": "uri", "pattern": "^https?://"}
    json = {"type": "object"}
    array = {"type": "array"}
    integer = {"type": "integer"}
    boolean = {"type": "boolean"}
    key_value_csv = {"type": "string", "is_key_value_csv": True}
    positive_integer = {"type": "integer", "minimum": 1}
    positive_or_null_integer = {"type": "integer", "minimum": 0}
    string_integer = {"type": "string", "pattern": "^([+-]?[1-9]\d*|0)$"}
    positive_string_integer = {"type": "string", "pattern": "^[1-9]\d*$"}
    positive_or_null_string_integer = {"type": "string", "pattern": "^\d+$"}

    @staticmethod
    def enum(accepted_values):
        return {"type": "string", "enum": accepted_values}


def _is_key_value_csv(validator, value, instance, schema):
    for element in instance.split(","):
        if len(element.split(":")) != 2:
            yield ValidationError("'%s' is not a 'key value csv'" % instance)


all_validators = dict(Draft4Validator.VALIDATORS)
all_validators["is_key_value_csv"] = _is_key_value_csv


def extend_with_default(validator_class):
    validate_properties = validator_class.VALIDATORS["properties"]

    def set_defaults(validator, properties, instance, schema):
        for property, subschema in properties.items():
            if "default" in subschema:
                instance.setdefault(property, subschema["default"])

        for error in validate_properties(validator, properties, instance, schema):
            yield error

    return validators.extend(validator_class, {"properties": set_defaults})


DCIValidator = extend_with_default(
    validators.create(Draft4Validator.META_SCHEMA, validators=all_validators)
)


def _get_error_message(error):
    if error.validator == "pattern":
        custom_error_messages = {
            "uuid": "is not a valid 'uuid'",
            "url": "is not a valid 'url'",
            "string_integer": "is not an integer",
            "positive_string_integer": "is not a positive integer",
            "positive_or_null_string_integer": "is not a positive or null integer",
        }
        property_name = error.relative_path[0]
        value = error.instance
        msg = custom_error_messages.get(property_name, error.message)
        return "%s: '%s' %s" % (property_name, value, msg)

    if (
        error.validator == "type"
        and error.validator_value in ["string", "array", "integer"]
    ) or (error.validator in ["minimum", "is_key_value_csv"]):
        property_name = error.path[-1]
        return "%s: %s" % (property_name, error.message)

    return error.message


def check_json_is_valid(schema, json):
    v = DCIValidator(schema, format_checker=FormatChecker())
    errors = []
    for error in sorted(v.iter_errors(json), key=str):
        errors.append(_get_error_message(error))
    if len(errors):
        raise DCIException("Request malformed", {"errors": errors, "error": errors[0]})


valid_resource_states = ["active", "inactive", "archived"]


###############################################################################
#                                                                             #
#                                 Args schema                                 #
#                                                                             #
###############################################################################
args_schema = {
    "type": "object",
    "properties": {
        "limit": with_default(Properties.positive_string_integer, None),
        "offset": with_default(Properties.positive_or_null_string_integer, None),
        "sort": Properties.string,
        "where": Properties.key_value_csv,
        "embed": Properties.string,
    },
    "dependencies": {
        "limit": {"required": ["offset"]},
        "offset": {"required": ["limit"]},
    },
    "additionalProperties": False,
}


def check_and_get_args(raw_args):
    check_json_is_valid(args_schema, raw_args)
    return parse_args(raw_args)


###############################################################################
#                                                                             #
#                                 User schemas                                #
#                                                                             #
###############################################################################
create_user_properties = {
    "name": Properties.string,
    "fullname": Properties.string,
    "email": Properties.email,
    "timezone": Properties.string,
    "password": Properties.string,
    "team_id": Properties.uuid,
    "state": with_default(Properties.enum(valid_resource_states), "active"),
}
create_user_schema = {
    "type": "object",
    "properties": create_user_properties,
    "required": ["name", "fullname", "email"],
    "additionalProperties": False,
}

update_user_properties = {
    "name": Properties.string,
    "fullname": Properties.string,
    "email": Properties.email,
    "timezone": Properties.string,
    "password": Properties.string,
    "team_id": Properties.uuid,
    "state": Properties.enum(valid_resource_states),
}
update_user_schema = {"type": "object", "properties": update_user_properties}

###############################################################################
#                                                                             #
#                            Current User schemas                             #
#                                                                             #
###############################################################################
update_current_user_schema = {
    "type": "object",
    "properties": {
        "current_password": Properties.string,
        "new_password": Properties.string,
        "fullname": Properties.string,
        "email": Properties.email,
        "timezone": Properties.string,
    },
}
