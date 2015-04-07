# -*- coding: utf-8 -*-
"""
    Normal settings file for Eve.

    Differently from a configuration file for an Eve application backed by Mongo
    we need to define the schema using the registerSchema decorator.

"""

from server.db.models import Base
from server.db.models import metadata

from eve_sqlalchemy.decorators import registerSchema


ID_FIELD = 'id'
ITEM_LOOKUP_FIELD = 'id'
ITEM_URL = 'regex("[-a-z0-9]{36,64}")'
LAST_UPDATED = "updated_at"
DATE_CREATED = "created_at"
ETAG = "etag"
SQLALCHEMY_DATABASE_URI = 'postgresql://boa:boa@127.0.0.1/dci_control_server'


DOMAIN = {}
for table in metadata.tables:
    print("table: %s" % table)
    DB = getattr(Base.classes, table)
    registerSchema(table)(DB)
    DOMAIN[table] = DB._eve_schema[table]
    DOMAIN[table].update({
        'id_field': ID_FIELD,
        'item_url': ITEM_URL,
        'item_lookup_field': ID_FIELD,
        'item_methods': ['PATCH', 'DELETE', 'GET'],
    })
    DOMAIN[table]['schema']['created_at']['required'] = False
    DOMAIN[table]['schema']['updated_at']['required'] = False
    DOMAIN[table]['schema']['etag']['required'] = False
    if hasattr(DB, 'name'):
        DOMAIN[table].update({
            'additional_lookup': {
                'url': 'regex("[\S]+")',
                'field': 'name'
            }})
# The following two lines will output the SQL statements
# executed by SQLAlchemy. Useful while debugging and in
# development. Turned off by default
# --------
# SQLALCHEMY_ECHO = True
# SQLALCHEMY_RECORD_QUERIES = True

DEBUG = True
