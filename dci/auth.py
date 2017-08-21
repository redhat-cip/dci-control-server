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
from passlib.apps import custom_app_context as pwd_context

from dci.db import models
from dci.common import exceptions as exc
from sqlalchemy import sql

UNAUTHORIZED = exc.DCIException('Operation not authorized.', status_code=401)


def hash_password(password):
    return pwd_context.encrypt(password)


def check_passwords_equal(password, encrypted_password):
    return pwd_context.verify(password, encrypted_password)


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


def user_role_in(user, roles=[]):
    """Return True if the user belongs to one of the roles."""

    role_ids = [get_role_id(label) for label in roles]
    return user['role_id'] in role_ids


def is_admin(user, super=False):
    if super and user['role_id'] == get_role_id('ADMIN'):
        return False
    return user['team_name'] == 'admin'


def is_admin_user(user, team_id):
    return is_in_team(user, team_id) and \
        user['role_id'] == get_role_id('ADMIN')


def is_in_parent_team(user, team_id, user_team_id):
    query = sql.select([models.TEAMS]).where(
        sql.and_(
            models.TEAMS.c.id == team_id,
            models.TEAMS.c.parent_id == user_team_id
        )
    )
    result = flask.g.db_conn.execute(query).fetchone()
    return result.id


def is_in_team(user, team_id):
    return str(user['team_id']) == str(team_id) or \
        is_in_parent_team(user, team_id, user['team_id'])


def check_export_control(user, component):
    if not is_admin(user):
        if not component['export_control']:
            raise UNAUTHORIZED
