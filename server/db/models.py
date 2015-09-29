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

import re

from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.automap import generate_relationship
from sqlalchemy import MetaData
from sqlalchemy.orm.interfaces import ONETOMANY
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

from eve_sqlalchemy.decorators import registerSchema


class DCIModel(object):

    def __init__(self, db_uri):
        # TODO(Gonéri): Load the value for a configuration file
        self.engine = create_engine(db_uri, pool_size=20, max_overflow=0,
                                    encoding='utf8', convert_unicode=True)

        self.metadata = MetaData()
        self.metadata.reflect(self.engine)

        for table in self.metadata.tables:
            print(table)

        # NOTE(Gonéri): ensure the associated resources list get sorted using
        # the created_at key.
        def _gen_relationship(base, direction, return_fn,
                              attrname, local_cls, referred_cls, **kw):
            if direction is ONETOMANY:
                kw['order_by'] = referred_cls.__table__.columns.created_at
            return generate_relationship(
                base, direction, return_fn,
                attrname, local_cls, referred_cls, **kw)
        self.base = automap_base(metadata=self.metadata)
        self.base.prepare(generate_relationship=_gen_relationship)

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
                print('%s.%s' % (cur_db, foreign_table_name))
                setattr(cur_db, foreign_table_name, relationship(
                    foreign_table_object, uselist=False,
                    remote_side=remote_side))

        from sqlalchemy.ext.associationproxy import association_proxy
        setattr(self.base.classes.jobdefinitions, 'components',
                association_proxy(
                    'jobdefinition_components_collection', 'component'))
        setattr(self.base.classes.jobs, 'jobstates', relationship(
            self.base.classes.jobstates, uselist=True, lazy='dynamic',
            order_by=self.base.classes.jobstates.created_at.desc()))
        self._Session = sessionmaker(bind=self.engine)

    def get_session(self):
        # NOTE(Gonéri): We should reuse the Flask-SQLAlchemy session here
        return self._Session()

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
            domain[table]['datasource']['default_sort'] = [('created_at', 1)]
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
        domain['jobs']['schema']['jobdefinition_id']['required'] = False
        domain['components']['datasource']['projection']['componenttype'] = 1

        # TODO(Gonéri): The following resource projection are enabled just to
        # be sure the resources will be embeddable. Instead we should make a
        # patch on Eve to dynamically turn on projection on embedded resources.
        domain['jobs']['datasource']['projection']['jobstates_collection'] = 1
        domain['jobdefinitions']['datasource']['projection']['components'] = 1
        from pprint import pprint
        pprint(domain)
        return domain
