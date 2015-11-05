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

import datetime
import hashlib
import uuid

import flask
import six
import sqlalchemy
from sqlalchemy import exc as sa_exc

from dci.server.common import exceptions


def json_encoder(obj):
    """Default JSON encoder."""

    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    elif isinstance(obj, uuid.UUID):
        return str(obj)


def gen_uuid():
    return str(uuid.uuid4())


def gen_etag():
    """Generate random etag based on uuid."""
    return gen_uuid()


def check_and_get_etag(headers):
    if_match_etag = headers.get('If-Match')
    if not if_match_etag:
        raise exceptions.DCIException("'If-match' header must be provided",
                                      status_code=412)
    return if_match_etag


def get_number_of_rows(table, where_cond=None):
    try:
        query = sqlalchemy.sql.select([sqlalchemy.func.count(table.c.id)])
        if where_cond is not None:
            query = query.where(where_cond)
        return flask.g.db_conn.execute(query).scalar()
    except sa_exc.DBAPIError as e:
        raise exceptions.DCIException(str(e), status_code=500)
