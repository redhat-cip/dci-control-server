# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Red Hat, Inc
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
import itertools
import pytz
import re
import six
import uuid
import voluptuous as v
from six.moves.urllib.parse import urlparse

from dci.common import exceptions


# Url validator is not powerfull enough let unleash its power
@v.message('expected a URL', cls=v.UrlInvalid)
def Url(value):
    try:
        parsed = urlparse(value)
        if not parsed.scheme or not parsed.netloc:
            raise v.UrlInvalid("must have a URL scheme and host")
        return value
    except Exception:
        raise ValueError


def UUID(value):
    try:
        if type(value) == uuid.UUID:
            return value
        else:
            return uuid.UUID(value)
    except Exception:
        raise ValueError


# Source of the regexp: http://emailregex.com/
def Email(value):
    try:
        pattern = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        if not re.match(pattern, value):
            raise Exception
        return value
    except Exception:
        raise ValueError


def Timezone(value):
    try:
        pytz.timezone(value)
        return value
    except Exception:
        raise ValueError


VALID_STATUS_UPDATE = ['new', 'pre-run', 'running', 'post-run',
                       'success', 'failure', 'killed', 'error']

VALID_RESOURCE_STATE = ['active', 'inactive', 'archived']

INVALID_LIST = 'not a valid list'
INVALID_UUID = 'not a valid uuid'
INVALID_JSON = 'not a valid json'
INVALID_STRING = 'not a valid string'
INVALID_URL = 'not a valid URL'
INVALID_EMAIL = 'not a valid email'
INVALID_TIMEZONE = 'not a valid timezone'

INVALID_PRODUCT = 'not a valid product id'
INVALID_TEAM = 'not a valid team id'
INVALID_TEST = 'not a valid test id'
INVALID_TOPIC = 'not a valid topic id'
INVALID_REMOTE_CI = 'not a valid remoteci id'
INVALID_JOB = 'not a valid job id'
INVALID_JOB_STATE = 'not a valid jobstate id'
INVALID_OFFSET = 'not a valid offset integer (must be greater than 0)'
INVALID_LIMIT = 'not a valid limit integer (must be greater than 0)'

INVALID_REQUIRED = 'required key not provided'
INVALID_OBJECT = 'not a valid object'
INVALID_STATUS_UPDATE = ('not a valid status update (must be %s)' %
                         ' or '.join(VALID_STATUS_UPDATE))
INVALID_RESOURCE_STATE = ('not a valid resource state (must be %s)' %
                          ' or '.join(VALID_RESOURCE_STATE))

INVALID_TYPE = 'not a valid string'

UUID_FIELD = v.All(six.text_type, msg=INVALID_UUID)
DATA_FIELD = {v.Optional('data', default={}): dict}


def dict_merge(*dict_list):
    """recursively merges dict's. not just simple a['key'] = b['key'], if
    both a and bhave a key who's value is a dict then dict_merge is called
    on both values and the result stored in the returned dictionary.
    """
    result = collections.defaultdict(dict)
    dicts_items = itertools.chain(*[six.iteritems(d or {}) for d in dict_list])

    for key, value in dicts_items:
        src = result[key]
        if isinstance(src, dict) and isinstance(value, dict):
            result[key] = dict_merge(src, value)
        elif isinstance(src, dict) or isinstance(src, six.text_type):
            result[key] = value
        elif hasattr(src, "__iter__") and hasattr(value, "__iter__"):
            result[key] += value
        else:
            result[key] = value

    return dict(result)


class Schema(v.Schema):
    """Override voluptuous schema to return our own error"""

    error_messages = {
        'expected dict': INVALID_JSON,
        'expected unicode': INVALID_STRING,
        'expected str': INVALID_STRING,
        'expected a URL': INVALID_URL,
        'expected a valid email': INVALID_EMAIL,
        'expected a dictionary': INVALID_OBJECT,
        'expected list': INVALID_LIST,
        'expected a valid timezone': INVALID_TIMEZONE
    }

    def __init__(self, schema, required=False, extra=v.REMOVE_EXTRA):
        super(Schema, self).__init__(schema, required, extra)

    def __call__(self, data):
        def format_error(error):
            msg = error.error_message
            error.error_message = self.error_messages.get(msg, msg)
            if error.path:
                path = six.text_type(error.path.pop())
                return {path: format_error(error)}
            else:
                return error.error_message

        try:
            return super(Schema, self).__call__(data)
        except v.MultipleInvalid as exc:
            errors = format_error(exc.errors.pop())
            for error in exc.errors:
                errors = dict_merge(errors, format_error(error))
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
#                                 Args schemas                                #
#                                                                             #
###############################################################################


split_coerce = v.Coerce(lambda s: [] if isinstance(s, list) else s.split(','))
args = Schema({
    v.Optional('limit', default=None): v.Any(v.All(v.Coerce(int), v.Range(0),
                                                   msg=INVALID_LIMIT), None),
    v.Optional('offset', default=None): v.Any(v.All(v.Coerce(int), v.Range(0),
                                                    msg=INVALID_OFFSET), None),
    v.Optional('sort', default=[]): split_coerce,
    v.Optional('where', default=[]): split_coerce,
    v.Optional('embed', default=[]): split_coerce
}, extra=v.REMOVE_EXTRA)

###############################################################################
#                                                                             #
#                                 Base schemas                                #
#                                                                             #
###############################################################################

base = {
    'name': six.text_type,
}


componenttype = schema_factory(base)

###############################################################################
#                                                                             #
#                                 Team schemas                                #
#                                                                             #
###############################################################################

team = dict_merge(base, {
    v.Optional('country', default=None): v.Any(six.text_type, None),
    v.Optional('state', default='active'): v.Any(*VALID_RESOURCE_STATE,
                                                 msg=INVALID_RESOURCE_STATE),
    v.Optional('external', default=True): bool,
    v.Optional('parent_id', default=None): v.Any(v.All(UUID, msg=INVALID_TEAM),
                                                 None),
})

team_put = {
    v.Optional('name'): six.text_type,
    v.Optional('country'): six.text_type,
    v.Optional('state'): v.Any(*VALID_RESOURCE_STATE,
                               msg=INVALID_RESOURCE_STATE),
    v.Optional('external'): bool,
    v.Optional('parent_id'): v.Any(UUID, msg=INVALID_TEAM),
}

team = DCISchema(schema_factory(team).post,
                 Schema(team_put))

###############################################################################
#                                                                             #
#                                 Test schemas                                #
#                                                                             #
###############################################################################

test = dict_merge(base, DATA_FIELD, {
    v.Optional('team_id'): v.Any(UUID, msg=INVALID_TEAM),
    v.Optional('state', default='active'): v.Any(*VALID_RESOURCE_STATE,
                                                 msg=INVALID_RESOURCE_STATE),
})

test_put = {
    v.Optional('name'): six.text_type,
    v.Optional('data'): dict,
    v.Optional('team_id'): v.Any(UUID, msg=INVALID_TEAM),
    v.Optional('state'): v.Any(*VALID_RESOURCE_STATE,
                               msg=INVALID_RESOURCE_STATE),
}

test = DCISchema(schema_factory(test).post, Schema(test_put))

###############################################################################
#                                                                             #
#                                 User schemas                                #
#                                                                             #
###############################################################################

user = dict_merge(base, {
    v.Optional('password'): six.text_type,
    'fullname': six.text_type,
    'email': v.Any(Email, msg=INVALID_EMAIL),
    v.Optional('team_id'): v.Any(UUID, msg=INVALID_TEAM),
    v.Optional('timezone'): v.Any(Timezone, msg=INVALID_TIMEZONE),
    v.Optional('state', default='active'): v.Any(*VALID_RESOURCE_STATE,
                                                 msg=INVALID_RESOURCE_STATE),
})

user_put = {
    v.Optional('name'): six.text_type,
    v.Optional('fullname'): six.text_type,
    v.Optional('email'): v.Any(Email, msg=INVALID_EMAIL),
    v.Optional('timezone'): v.Any(Timezone, msg=INVALID_TIMEZONE),
    v.Optional('password'): six.text_type,
    v.Optional('team_id'): v.Any(UUID, msg=INVALID_TEAM),
    v.Optional('state'): v.Any(*VALID_RESOURCE_STATE,
                               msg=INVALID_RESOURCE_STATE),
}

user = DCISchema(schema_factory(user).post, Schema(user_put))

###############################################################################
#                                                                             #
#                            Current User schemas                             #
#                                                                             #
###############################################################################

current_user_put = {
    'current_password': six.text_type,
    v.Optional('new_password'): six.text_type,
    v.Optional('fullname'): six.text_type,
    v.Optional('email'): v.Any(Email, msg=INVALID_EMAIL),
    v.Optional('timezone'): v.Any(Timezone, msg=INVALID_TIMEZONE),
}

current_user = DCISchema(schema_factory({}).post, Schema(current_user_put))


###############################################################################
#                                                                             #
#                              Component schemas                              #
#                                                                             #
###############################################################################

component = dict_merge(base, DATA_FIELD, {
    v.Optional('title', default=None): v.Any(six.text_type, None),
    v.Optional('message', default=None): v.Any(six.text_type, None),
    v.Optional('canonical_project_name', default=None): v.Any(six.text_type,
                                                              None),
    # True if the component can be exported to non US countries.
    v.Optional('export_control', default=False): bool,
    v.Optional('url', default=None): v.Any(Url(), None),
    'type': six.text_type,
    'topic_id': v.Any(UUID, msg=INVALID_TOPIC),
    v.Optional('state', default='active'): v.Any(*VALID_RESOURCE_STATE,
                                                 msg=INVALID_RESOURCE_STATE),
})

component_put = {
    v.Optional('name'): six.text_type,
    v.Optional('export_control'): bool,
    v.Optional('data'): dict,
    v.Optional('title'): six.text_type,
    v.Optional('message'): six.text_type,
    v.Optional('canonical_project_name'): six.text_type,
    v.Optional('url'): v.Any(None, Url()),
    v.Optional('type'): six.text_type,
    v.Optional('state'): v.Any(*VALID_RESOURCE_STATE,
                               msg=INVALID_RESOURCE_STATE),
}

component = DCISchema(schema_factory(component).post,
                      Schema(component_put))

###############################################################################
#                                                                             #
#                             Remote CI schemas                               #
#                                                                             #
###############################################################################

remoteci = dict_merge(base, DATA_FIELD, {
    'team_id': v.Any(UUID, msg=INVALID_TEAM),
    v.Optional('public', default=False): bool,
    v.Optional('state', default='active'): v.Any(*VALID_RESOURCE_STATE,
                                                 msg=INVALID_RESOURCE_STATE),
})

remoteci_put = {
    v.Optional('name'): six.text_type,
    v.Optional('data'): dict,
    v.Optional('team_id'): v.Any(UUID, msg=INVALID_TEAM),
    v.Optional('public'): bool,
    v.Optional('state'): v.Any(*VALID_RESOURCE_STATE,
                               msg=INVALID_RESOURCE_STATE),
}

remoteci = DCISchema(schema_factory(remoteci).post, Schema(remoteci_put))


###############################################################################
#                                                                             #
#                                Job schemas                                  #
#                                                                             #
###############################################################################

job = {
    v.Optional('remoteci_id'): v.Any(UUID, msg=INVALID_REMOTE_CI),
    v.Optional('team_id'): v.Any(UUID, msg=INVALID_TEAM),
    'components': list,
    v.Optional('comment', default=None): v.Any(six.text_type, None),
    v.Optional('previous_job_id', default=None): v.Any(v.All(UUID,
                                                             msg=INVALID_JOB),
                                                       None),
    v.Optional('update_previous_job_id', default=None): v.Any(
        v.All(UUID, msg=INVALID_JOB), None
    ),
    v.Optional('state', default='active'): v.Any(*VALID_RESOURCE_STATE,
                                                 msg=INVALID_RESOURCE_STATE),
    v.Optional('topic_id', default=None): v.Any(v.All(UUID, msg=INVALID_TOPIC),
                                                None),
    v.Optional('topic_id_secondary', default=None): v.Any(v.All(UUID, msg=INVALID_TOPIC),  # noqa
                                                None),
}

job_put = {
    v.Optional('comment'): six.text_type,
    v.Optional('status'): v.Any(*VALID_STATUS_UPDATE,
                                msg=INVALID_STATUS_UPDATE),
    v.Optional('state'): v.Any(*VALID_RESOURCE_STATE,
                               msg=INVALID_RESOURCE_STATE),
}

job = DCISchema(schema_factory(job).post, Schema(job_put))

job_schedule = {
    v.Optional('remoteci_id'): v.Any(UUID, msg=INVALID_REMOTE_CI),
    v.Optional('dry_run', default=False): bool,
    'topic_id': v.Any(UUID, msg=INVALID_TOPIC),
    v.Optional('topic_id_secondary', default=None): v.Any(v.All(UUID,
                                                          msg=INVALID_TOPIC),
                                                          None),
    v.Optional('components_ids', default=[]): list
}

job_schedule = schema_factory(job_schedule)


job_upgrade = {
    'job_id': v.Any(UUID, msg=INVALID_JOB)
}

job_upgrade = schema_factory(job_upgrade)


job_schedule_template = {
    v.Optional('remoteci_id'): v.Any(UUID, msg=INVALID_REMOTE_CI),
    'topic_id': v.Any(UUID, msg=INVALID_TOPIC),

}

job_schedule_template = schema_factory(job_schedule_template)

###############################################################################
#                                                                             #
#                             Job State schemas                               #
#                                                                             #
###############################################################################

jobstate = {
    'status': six.text_type,
    'job_id': v.Any(UUID, msg=INVALID_JOB),
    v.Optional('comment', default=None): v.Any(six.text_type, None),
}

jobstate = schema_factory(jobstate)

###############################################################################
#                                                                             #
#                                File schemas                                 #
#                                                                             #
###############################################################################

file = dict_merge(base, {
    v.Optional('content', default=''): six.text_type,
    v.Optional('md5', default=None): v.Any(six.text_type, None),
    v.Optional('mime', default=None): v.Any(six.text_type, None),
    v.Optional('jobstate_id', default=None): v.Any(
        v.All(UUID, msg=INVALID_JOB_STATE), None
    ),
    v.Optional('job_id', default=None): v.Any(
        v.All(UUID, msg=INVALID_JOB), None
    ),
    v.Optional('state', default='active'): v.Any(*VALID_RESOURCE_STATE,
                                                 msg=INVALID_RESOURCE_STATE),
    v.Optional('test_id', default=None): v.Any(
        v.All(UUID, msg=INVALID_TEST), None
    )
})

file = schema_factory(file)

file_upload_certification = schema_factory({
    'username': six.text_type,
    'password': six.text_type,
    'certification_id': six.text_type,
})

###############################################################################
#                                                                             #
#                                Topic schemas                                #
#                                                                             #
###############################################################################

topic = dict_merge(base, DATA_FIELD, {
    'product_id': v.Any(
        v.All(UUID, msg=INVALID_PRODUCT), None
    ),
    v.Optional('next_topic_id', default=None): v.Any(
        v.All(UUID, msg=INVALID_TOPIC), None
    ),
    v.Optional('state', default='active'): v.Any(*VALID_RESOURCE_STATE,
                                                 msg=INVALID_RESOURCE_STATE),
    v.Optional('component_types', default=[]): list,
    v.Optional('export_control', default=False): bool,
})

topic_put = {
    v.Optional('name'): six.text_type,
    v.Optional('next_topic_id'): v.Any(None, UUID, msg=INVALID_TOPIC),
    v.Optional('product_id'): v.Any(UUID, msg=INVALID_PRODUCT),
    v.Optional('state'): v.Any(*VALID_RESOURCE_STATE,
                               msg=INVALID_RESOURCE_STATE),
    v.Optional('component_types'): list,
    v.Optional('data'): dict,
    v.Optional('export_control'): bool,
}

topic = DCISchema(schema_factory(topic).post, Schema(topic_put))

###############################################################################
#                                                                             #
#                               Audit schemas                                 #
#                                                                             #
###############################################################################

audit = {
    v.Optional('limit', default=10): int
}

audit = schema_factory(audit)

###############################################################################
#                                                                             #
#                                Issues schemas                               #
#                                                                             #
###############################################################################

issue = {
    'url': Url(),
    v.Optional('topic_id', default=None): v.Any(UUID, msg=INVALID_TOPIC),
}

issue = schema_factory(issue)

issue_test = {
    v.Optional('test_id'): v.Any(UUID, msg=INVALID_UUID),
}

issue_test = schema_factory(issue_test)

###############################################################################
#                                                                             #
#                                Metas schemas                                #
#                                                                             #
###############################################################################

meta = {
    'name': six.text_type,
    v.Optional('value'): six.text_type
}

meta_put = {
    v.Optional('name'): six.text_type,
    v.Optional('value'): six.text_type
}

meta = DCISchema(schema_factory(meta).post, Schema(meta_put))

###############################################################################
#                                                                             #
#                                Tags schemas                                 #
#                                                                             #
###############################################################################

tag = {
    'name': six.text_type,
}

tag_put = {
}

tag = DCISchema(schema_factory(tag).post, Schema(tag_put))
###############################################################################
#                                                                             #
#                                Roles schemas                                #
#                                                                             #
###############################################################################

role = {
    'name': six.text_type,
    v.Optional('label', default=None): v.Any(six.text_type, None),
    v.Optional('description', default=None): v.Any(six.text_type, None),
    v.Optional('state', default='active'): v.Any(*VALID_RESOURCE_STATE,
                                                 msg=INVALID_RESOURCE_STATE),
}

role_put = {
    v.Optional('name'): six.text_type,
    v.Optional('description'): six.text_type,
    v.Optional('state'): v.Any(*VALID_RESOURCE_STATE,
                               msg=INVALID_RESOURCE_STATE),
}

role = DCISchema(schema_factory(role).post, Schema(role_put))


###############################################################################
#                                                                             #
#                          Permissions schemas                                #
#                                                                             #
###############################################################################

permission = {
    'name': six.text_type,
    v.Optional('label', default=None): v.Any(six.text_type, None),
    v.Optional('description', default=None): v.Any(six.text_type, None),
    v.Optional('state', default='active'): v.Any(*VALID_RESOURCE_STATE,
                                                 msg=INVALID_RESOURCE_STATE),
}

permission_put = {
    v.Optional('name'): six.text_type,
    v.Optional('description'): six.text_type,
    v.Optional('state'): v.Any(*VALID_RESOURCE_STATE,
                               msg=INVALID_RESOURCE_STATE),
}

permission = DCISchema(schema_factory(permission).post, Schema(permission_put))

###############################################################################
#                                                                             #
#                             Products schemas                                #
#                                                                             #
###############################################################################

product = {
    'name': six.text_type,
    'team_id': v.Any(UUID, msg=INVALID_TEAM),
    v.Optional('label', default=None): v.Any(six.text_type, None),
    v.Optional('description', default=None): v.Any(six.text_type, None),
    v.Optional('state', default='active'): v.Any(*VALID_RESOURCE_STATE,
                                                 msg=INVALID_RESOURCE_STATE),
}

product_put = {
    v.Optional('name'): six.text_type,
    v.Optional('description'): six.text_type,
    v.Optional('state'): v.Any(*VALID_RESOURCE_STATE,
                               msg=INVALID_RESOURCE_STATE),
    v.Optional('team_id'): v.Any(UUID, msg=INVALID_TEAM),
}

product = DCISchema(schema_factory(product).post, Schema(product_put))

###############################################################################
#                                                                             #
#                             Feeder schemas                                  #
#                                                                             #
###############################################################################

feeder = dict_merge(base, DATA_FIELD, {
    'team_id': v.Any(UUID, msg=INVALID_TEAM),
    v.Optional('state', default='active'): v.Any(*VALID_RESOURCE_STATE,
                                                 msg=INVALID_RESOURCE_STATE),
})

feeder_put = {
    v.Optional('name'): six.text_type,
    v.Optional('data'): dict,
    v.Optional('team_id'): v.Any(UUID, msg=INVALID_TEAM),
    v.Optional('state'): v.Any(*VALID_RESOURCE_STATE,
                               msg=INVALID_RESOURCE_STATE),
}

feeder = DCISchema(schema_factory(feeder).post, Schema(feeder_put))

###############################################################################
#                                                                             #
#                          Fingerprints schemas                               #
#                                                                             #
###############################################################################

fingerprint = dict_merge(base, {
    'fingerprint': dict,
    'actions': dict,
    'description': six.text_type,
    'topic_id': v.Any(UUID, msg=INVALID_TOPIC),
    v.Optional('state', default='active'): v.Any(*VALID_RESOURCE_STATE,
                                                 msg=INVALID_RESOURCE_STATE),
})

fingerprint_put = {
    v.Optional('name'): six.text_type,
    v.Optional('fingerprint'): dict,
    v.Optional('actions'): dict,
    v.Optional('description'): six.text_type,
    v.Optional('state'): v.Any(*VALID_RESOURCE_STATE,
                               msg=INVALID_RESOURCE_STATE),
}

fingerprint = DCISchema(schema_factory(fingerprint).post,
                        Schema(fingerprint_put))

###############################################################################
#                                                                             #
#                          Counter schemas                                    #
#                                                                             #
###############################################################################

counter_put = {
    'sequence': int
}

counter = DCISchema(None, Schema(counter_put))

###############################################################################
#                                                                             #
#                             Analytics schemas                               #
#                                                                             #
###############################################################################

analytic = {
    'name': six.text_type,
    'type': six.text_type,
    v.Optional('url', default=None): six.text_type,
    v.Optional('data'): dict,
}

analytic_put = {
    v.Optional('name'): six.text_type,
    v.Optional('type'): six.text_type,
    v.Optional('url', default=None): six.text_type,
    v.Optional('data'): dict,
}

analytic = DCISchema(schema_factory(analytic).post,
                     Schema(analytic_put))
