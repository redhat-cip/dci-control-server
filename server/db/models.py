# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 eNovance SAS <licensing@enovance.com>
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

import re

from sqlalchemy import create_engine
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import MetaData
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from eve_sqlalchemy.decorators import registerSchema


class DCIModel(object):

    def __init__(self, db_uri):
        # TODO(Gonéri): Load the value for a configuration file
        self.engine = create_engine(db_uri, pool_size=20, max_overflow=10,
                                    pool_reset_on_return='rollback')

        self.metadata = MetaData()
        self.metadata.reflect(self.engine)

        for table in self.metadata.tables:
            print(table)

        self.base = automap_base(metadata=self.metadata)
        self.base.prepare()

        # engine.echo = True

        # NOTE(Gonéri): Create the foreign table attribue to be able to
        # do job.remoteci.name
        for table in self.metadata.tables:
            cur_db = getattr(self.base.classes, table)
            for column in cur_db.__table__.columns:
                m = re.search(r"\.(\w+)_id$", str(column))
                if not m:
                    continue
                foreign_table_name = m.group(1)
                foreign_table_object = getattr(
                    self.base.classes, foreign_table_name + 's')
                remote_side = None
                remote_side = [foreign_table_object.id]
                setattr(cur_db, foreign_table_name, relationship(
                    foreign_table_object, uselist=False,
                    remote_side=remote_side))

        setattr(self.base.classes.products, 'versions', relationship(
            self.base.classes.versions, uselist=True, lazy='dynamic'))
        setattr(self.base.classes.versions, 'notifications', relationship(
            self.base.classes.notifications, uselist=True, lazy='dynamic'))

        setattr(self.base.classes.users, 'roles', association_proxy(
                'user_roles_collection', 'role'))

    def get_session(self):
        return Session(self.engine)

    def get_table_description(self, table):
        """Prepare a table description for Eve-Docs
        See: https://github.com/hermannsblum/eve-docs
        """
        cur_db = getattr(self.base.classes, table)
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
        for row in self.engine.execute(table_description_query, table=table):
            if row[0] == 0:
                result['general'] = row[1]
            else:
                result['fields'][fields[row[0]]] = row[1]
        return result

    def generate_eve_domain_configuration(self):
        domain = {}
        for table in self.metadata.tables:
            DB = getattr(self.base.classes, table)
            registerSchema(table)(DB)
            domain[table] = DB._eve_schema[table]
            domain[table].update({
                'id_field': 'id',
                'item_url': 'regex("[-a-z0-9]{8}-[-a-z0-9]{4}-'
                            '[-a-z0-9]{4}-[-a-z0-9]{4}-[-a-z0-9]{12}")',
                'item_lookup_field': 'id',
                'resource_methods': ['GET', 'POST', 'DELETE'],
                'item_methods': ['PATCH', 'DELETE', 'PUT', 'GET'],
                'public_methods': [],
                'public_item_methods': [],
            })
            domain[table]['schema']['created_at']['required'] = False
            domain[table]['schema']['updated_at']['required'] = False
            domain[table]['schema']['etag']['required'] = False
            if 'team_id' in domain[table]['schema']:
                domain[table]['schema']['team_id']['required'] = False
                domain[table]['auth_field'] = 'team_id'
            if hasattr(DB, 'name'):
                domain[table].update({
                    'additional_lookup': {
                        'url': 'regex("[-_\w\d]+")',
                        'field': 'name'
                    }})
            domain[table]['description'] = self.get_table_description(table)
        # NOTE(Goneri): optional, if the key is missing, we dynamically pick
        # a testversion that fit.
        domain['jobs']['schema']['testversion_id']['required'] = False
        return domain
