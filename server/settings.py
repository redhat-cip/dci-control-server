# -*- coding: utf-8 -*-
#
# Copyright 2015 Red Hat, Inc.
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

"""
    Normal settings file for Eve.

    Differently from a configuration file for an Eve application backed by
    Mongo we need to define the schema using the registerSchema decorator.

"""

import os

from server.db.models import Base
from server.db.models import engine
from server.db.models import metadata

from eve_sqlalchemy.decorators import registerSchema
from sqlalchemy.sql import text


ID_FIELD = 'id'
ITEM_LOOKUP_FIELD = 'id'
ITEM_URL = 'regex("[-a-z0-9]{36,64}")'
LAST_UPDATED = "updated_at"
DATE_CREATED = "created_at"
ETAG = "etag"
SQLALCHEMY_DATABASE_URI = os.environ.get(
    'OPENSHIFT_POSTGRESQL_DB_URL',
    'postgresql://boa:boa@127.0.0.1:5432/dci_control_server')


DOMAIN = {}


def get_table_description(table):
    """Prepare a table description for Eve-Docs
    See: https://github.com/hermannsblum/eve-docs
    """
    cur_db = getattr(Base.classes, table)
    fields = []
    for column in cur_db.__table__.columns:
        fields.append(str(column).split('.')[1])

    table_description_query = text("""
SELECT
    objsubid, description
FROM
    pg_description WHERE objoid = :table ::regclass;
""")
    result = {
        'general': '',
        'fields': {}
    }
    for row in engine.execute(table_description_query, table=table):
        print(row[0])
        if row[0] == 0:
            result['general'] = row[1]
        else:
            result['fields'][fields[row[0]]] = row[1]
    return result

for table in metadata.tables:
    DB = getattr(Base.classes, table)
    registerSchema(table)(DB)
    DOMAIN[table] = DB._eve_schema[table]
    DOMAIN[table].update({
        'id_field': ID_FIELD,
        'item_url': ITEM_URL,
        'item_lookup_field': ID_FIELD,
        'resource_methods': ['GET', 'POST', 'DELETE'],
        'item_methods': ['PATCH', 'DELETE', 'PUT', 'GET'],
        'public_methods': [],
        'public_item_methods': [],
    })
    DOMAIN[table]['schema']['created_at']['required'] = False
    DOMAIN[table]['schema']['updated_at']['required'] = False
    DOMAIN[table]['schema']['etag']['required'] = False
    if 'team_id' in DOMAIN[table]['schema']:
        DOMAIN[table]['schema']['team_id']['required'] = False
        DOMAIN[table]['auth_field'] = 'team_id'
    if hasattr(DB, 'name'):
        DOMAIN[table].update({
            'additional_lookup': {
                'url': 'regex("[\S]+")',
                'field': 'name'
            }})
    DOMAIN[table]['description'] = get_table_description(table)
# The following two lines will output the SQL statements
# executed by SQLAlchemy. Useful while debugging and in
# development. Turned off by default
# --------
# SQLALCHEMY_ECHO = True
# SQLALCHEMY_RECORD_QUERIES = True

# NOTE(Goneri): optional, if the key is missing, we dynamically pick
# a testversion that fit.
DOMAIN['jobs']['schema']['testversion_id']['required'] = False

DEBUG = True
URL_PREFIX = 'api'
X_DOMAINS = '*'
X_HEADERS = 'Authorization'
