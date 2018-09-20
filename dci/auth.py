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

import flask
import jwt
from passlib.apps import custom_app_context as pwd_context

from dci.db import models
from dci.common import exceptions as exc
from sqlalchemy import sql

UNAUTHORIZED = exc.DCIException('Operation not authorized.', status_code=401)


def hash_password(password):
    return pwd_context.encrypt(password)


def check_passwords_equal(password, encrypted_password):
    return pwd_context.verify(password, encrypted_password)


def decode_jwt(access_token, pem_public_key, audience):
    return jwt.decode(access_token, verify=True, key=pem_public_key,
                      audience=audience, algorithms=['RS256'])


# This method should be deleted once permissions mechanism is
# in place. Meanwhile, for the migration to be seamless, we
# need to have this method around
def get_role_id(label):
    """Return role id based on role label."""

    query = sql.select([models.ROLES]).where(
        models.ROLES.c.label == label
    )
    result = flask.g.db_conn.execute(query).fetchone()
    return result.id


def check_export_control(user, component):
    if user.is_not_super_admin() and not component['export_control']:
        raise UNAUTHORIZED
