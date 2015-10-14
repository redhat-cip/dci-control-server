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
from sqlalchemy import Column
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from sqlalchemy.types import DateTime
from sqlalchemy.types import String


class DCIModel(object):
    Base = declarative_base()

    class DCIBase(Base):
        __abstract__ = True
        id = Column(UUID, primary_key=True)
        created_at = Column(DateTime(timezone=True),
                            default=datetime.datetime.utcnow, nullable=False)
        updated_at = Column(DateTime(timezone=True),
                            onupdate=datetime.datetime.utcnow,
                            default=datetime.datetime.utcnow, nullable=False)
        etag = Column(String(40), default=func.gen_etag(), nullable=False)

    class Team(DCIBase):
        __tablename__ = 'teams'
        name = Column(String(100))

    class Componenttype(DCIBase):
        __tablename__ = 'componenttypes'
        name = Column(String(100))

    class User(DCIBase):
        __tablename__ = 'users'
        name = Column(String(100))
        password = Column(String())
        team_id = Column(UUID(), ForeignKey('teams.id'))

    class Test(DCIBase):
        __tablename__ = 'tests'
        data = Column(JSON())
        name = Column(String(255))

    class Role(DCIBase):
        __tablename__ = 'roles'
        name = Column(String(100))

    class UserRole(DCIBase):
        __tablename__ = 'user_roles'
        user_id = Column(UUID(), ForeignKey('users.id'))
        role_id = Column(UUID(), ForeignKey('roles.id'))

    class Remoteci(DCIBase):
        __tablename__ = 'remotecis'
        name = Column(String(100))
        data = Column(JSON())
        team_id = Column(UUID(), ForeignKey('teams.id'))
        test_id = Column(UUID(), ForeignKey('tests.id'))
        team = relationship('Team', uselist=False)
        test = relationship('Test', uselist=False)

    class Jobdefinition(DCIBase):
        __tablename__ = 'jobdefinitions'
        name = Column(String(100))
        test_id = Column(UUID(), ForeignKey('tests.id'))
        test = relationship('Test', uselist=False)

    class Job(DCIBase):
        __tablename__ = 'jobs'
        remoteci_id = Column(UUID(), ForeignKey('remotecis.id'))
        team_id = Column(UUID(), ForeignKey('teams.id'))
        remoteci = relationship('Remoteci', uselist=False)
        jobdefinition_id = Column(UUID(), ForeignKey('jobdefinitions.id'))
        jobdefinition = relationship('Jobdefinition', uselist=False)

    class Jobstate(DCIBase):
        __tablename__ = 'jobstates'
        comment = Column(String())
        job_id = Column(UUID(), ForeignKey('jobs.id'))
        team_id = Column(UUID(), ForeignKey('teams.id'))
        status = Column(String(), default='ongoing')

    class File(DCIBase):
        __tablename__ = 'files'
        name = Column(String(100))
        content = Column(String())
        mime = Column(String(100), default='text/plain')
        md5 = Column(String(32))
        jobstate_id = Column(UUID(), ForeignKey('jobstates.id'))
        team_id = Column(UUID(), ForeignKey('teams.id'))

    class Component(DCIBase):
        __tablename__ = 'components'
        name = Column(String(100))
        componenttype_id = Column(UUID(), ForeignKey('componenttypes.id'))
        data = Column(JSON())
        sha = Column(String())
        title = Column(String())
        message = Column(String())
        url = Column(String())
        git = Column(String())
        ref = Column(String())
        canonical_project_name = Column(String())
        componenttype = relationship('Componenttype', uselist=False)

    class JobdefinitionComponent(DCIBase):
        __tablename__ = 'jobdefinition_components'
        component_id = Column(UUID(), ForeignKey('components.id'))
        jobdefinition_id = Column(UUID(), ForeignKey('jobdefinitions.id'))
        component = relationship('Component', uselist=False)
        jobdefinition = relationship('Jobdefinition', uselist=False)

    setattr(Jobdefinition, 'jobs', relationship(
        Job, uselist=True))
    setattr(Jobdefinition, 'jobdefinition_components', relationship(
        JobdefinitionComponent))
    setattr(Jobdefinition, 'components',
            association_proxy(
                'jobdefinition_components', 'component'))
    setattr(Job, 'jobstates', relationship(
        Jobstate,
        order_by=Jobstate.created_at.desc()))
    setattr(User, 'user_roles', relationship(
        UserRole))
    setattr(User, 'roles',
            association_proxy(
                'user_roles', 'role'))


    def __init__(self, db_uri):

        # TODO(Gonéri): Load the value for a configuration file
        self.engine = create_engine(db_uri, pool_size=20, max_overflow=0,
                                    encoding='utf8', convert_unicode=True)
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
        uuid_re = ('regex("[-a-z0-9]{8}-[-a-z0-9]{4}-' +
                   '[-a-z0-9]{4}-[-a-z0-9]{4}-[-a-z0-9]{12}")')
        name_re = 'regex("[-_\\w\\d]+")'
        domain = {
            'components': {
                'additional_lookup': {
                    'field': 'name',
                    'url': name_re},
                'datasource': {
                    'default_sort': [('created_at', 1)],
                    'projection': {
                        'canonical_project_name': 1,
                        'componenttype': 1,
                        'componenttype_id': 0,
                        'created_at': 1,
                        'data': 1,
                        'etag': 1,
                        'git': 1,
                        'id': 1,
                        'message': 1,
                        'name': 1,
                        'ref': 1,
                        'sha': 1,
                        'title': 1,
                        'updated_at': 1,
                        'url': 1},
                    'source': 'Component'},
                'description': {
                    'fields': {}, 'general': 'The components.'},
                'id_field': 'id',
                'item_lookup': True,
                'item_lookup_field': 'id',
                'item_methods': ['PATCH', 'DELETE', 'PUT', 'GET'],
                'item_url': uuid_re,
                'public_item_methods': [],
                'public_methods': [],
                'resource_methods': ['GET', 'POST', 'DELETE'],
                'schema': {
                    'canonical_project_name': {
                        'required': True,
                        'type': 'string',
                        'unique': False},
                    'componenttype': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'componenttypes'},
                        'type': 'objectid'},
                    'componenttype_id': {
                        'data_relation': {
                            'embeddable': False,
                            'resource': 'componenttypes'},
                        'required': True,
                        'type': 'objectid',
                        'unique': False},
                    'created_at': {
                        'required': False,
                        'type': 'datetime',
                        'unique': False},
                    'data': {
                        'nullable': True,
                        'required': False,
                        'type': 'json',
                        'unique': False},
                    'etag': {
                        'maxlength': 40,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'git': {
                        'nullable': True,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'id': {
                        'required': False,
                        'type': 'string',
                        'unique': True},
                    'message': {
                        'nullable': True,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'name': {
                        'maxlength': 255,
                        'required': True,
                        'type': 'string',
                        'unique': False},
                    'ref': {
                        'nullable': True,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'sha': {
                        'nullable': True,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'title': {
                        'nullable': True,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'updated_at': {
                        'required': False,
                        'type': 'datetime',
                        'unique': False},
                    'url': {
                        'nullable': True,
                        'required': False,
                        'type': 'string',
                        'unique': False}}},
            'componenttypes': {
                'additional_lookup': {
                    'field': 'name',
                    'url': name_re},
                'datasource': {
                    'default_sort': [('created_at', 1)],
                    'projection': {
                        'components': 0,
                        'created_at': 1,
                        'etag': 1,
                        'id': 1,
                        'name': 1,
                        'updated_at': 1},
                    'source': 'Componenttype'},
                'description': {
                    'fields': {},
                    'general': 'The different type of '
                    'components.'},
                'id_field': 'id',
                'item_lookup': True,
                'item_lookup_field': 'id',
                'item_methods': ['PATCH', 'DELETE', 'PUT', 'GET'],
                'item_url': uuid_re,
                'public_item_methods': [],
                'public_methods': [],
                'resource_methods': ['GET', 'POST', 'DELETE'],
                'schema': {
                    'components': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'components'},
                        'type': 'objectid'},
                    'created_at': {
                        'required': False,
                        'type': 'datetime',
                        'unique': False},
                    'etag': {
                        'maxlength': 40,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'id': {
                        'required': False,
                        'type': 'string',
                        'unique': True},
                    'name': {
                        'maxlength': 255,
                        'required': True,
                        'type': 'string',
                        'unique': False},
                    'updated_at': {
                        'required': False,
                        'type': 'datetime',
                        'unique': False}}},
            'files': {
                'additional_lookup': {
                    'field': 'name',
                    'url': name_re},
                'auth_field': 'team_id',
                'datasource': {
                    'default_sort': [('created_at', 1)],
                    'projection': {
                        'content': 1,
                        'created_at': 1,
                        'etag': 1,
                        'id': 1,
                        'jobstate': 1,
                        'jobstate_id': 0,
                        'md5': 1,
                        'mime': 1,
                        'name': 1,
                        'team': 0,
                        'team_id': 1,
                        'teams': 0,
                        'updated_at': 1},
                    'source': 'File'},
                'description': {
                    'fields': {},
                    'general': 'The output of a command execution. '
                    'The file is associated to a '
                    'jobstate of a given job.'},
                'id_field': 'id',
                'item_lookup': True,
                'item_lookup_field': 'id',
                'item_methods': ['PATCH', 'DELETE', 'PUT', 'GET'],
                'item_url': uuid_re,
                'public_item_methods': [],
                'public_methods': [],
                'resource_methods': ['GET', 'POST', 'DELETE'],
                'schema': {
                    'content': {
                        'required': True,
                        'type': 'string',
                        'unique': False},
                    'created_at': {
                        'required': False,
                        'type': 'datetime',
                        'unique': False},
                    'etag': {
                        'maxlength': 40,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'id': {
                        'required': False,
                        'type': 'string',
                        'unique': True},
                    'jobstate': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'jobstates'},
                        'type': 'objectid'},
                    'jobstate_id': {
                        'data_relation': {
                            'embeddable': False,
                            'resource': 'jobstates'},
                        'required': True,
                        'type': 'objectid',
                        'unique': False},
                    'md5': {
                        'maxlength': 32,
                        'nullable': True,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'mime': {
                        'maxlength': 100,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'name': {
                        'maxlength': 512,
                        'required': True,
                        'type': 'string',
                        'unique': False},
                    'team': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'teams'},
                        'type': 'objectid'},
                    'team_id': {
                        'data_relation': {
                            'embeddable': False,
                            'resource': 'teams'},
                        'required': False,
                        'type': 'objectid',
                        'unique': False},
                    'teams': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'teams'},
                        'type': 'objectid'},
                    'updated_at': {
                        'required': False,
                        'type': 'datetime',
                        'unique': False}}},
            'jobdefinition_components': {
                'datasource': {
                    'default_sort': [('created_at',
                                      1)],
                    'projection': {
                        'component': 1,
                        'component_id': 0,
                        'created_at': 1,
                        'etag': 1,
                        'id': 1,
                        'jobdefinition': 1,
                        'jobdefinition_id': 0,
                        'updated_at': 1},
                    'source': 'JobdefinitionComponent'},
                'description': {
                    'fields': {}, 'general': ''},
                'id_field': 'id',
                'item_lookup': True,
                'item_lookup_field': 'id',
                'item_methods': ['PATCH',
                                 'DELETE',
                                 'PUT',
                                 'GET'],
                'item_url': uuid_re,
                'public_item_methods': [],
                'public_methods': [],
                'resource_methods': ['GET', 'POST', 'DELETE'],
                'schema': {
                    'component': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'components'},
                        'type': 'objectid'},
                    'component_id': {
                        'data_relation': {
                            'embeddable': False,
                            'resource': 'components'},
                        'required': True,
                        'type': 'objectid',
                        'unique': False},
                    'created_at': {
                        'required': False,
                        'type': 'datetime',
                        'unique': False},
                    'etag': {
                        'maxlength': 40,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'id': {
                        'required': False,
                        'type': 'string',
                        'unique': True},
                    'jobdefinition': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'jobdefinitions'},
                        'type': 'objectid'},
                    'jobdefinition_id': {
                        'data_relation': {
                            'embeddable': False,
                            'resource': 'jobdefinitions'},
                        'required': True,
                        'type': 'objectid',
                        'unique': False},
                    'updated_at': {
                        'required': False,
                        'type': 'datetime',
                        'unique': False}}},
            'jobdefinitions': {
                'additional_lookup': {
                    'field': 'name',
                    'url': name_re},
                'datasource': {
                    'default_sort': [('created_at', 1)],
                    'projection': {
                        'components': 1,
                        'created_at': 1,
                        'etag': 1,
                        'id': 1,
                        'jobs': 0,
                        'name': 1,
                        'test': 1,
                        'test_id': 0,
                        'updated_at': 1},
                    'source': 'Jobdefinition'},
                'description': {
                    'fields': {}, 'general': ''},
                'id_field': 'id',
                'item_lookup': True,
                'item_lookup_field': 'id',
                'item_methods': ['PATCH', 'DELETE', 'PUT', 'GET'],
                'item_url': uuid_re,
                'public_item_methods': [],
                'public_methods': [],
                'resource_methods': ['GET', 'POST', 'DELETE'],
                'schema': {
                    'components': {
                        'schema': {
                            'data_relation': {
                                'embeddable': True,
                                'resource': 'components'},
                            'type': 'objectid'},
                        'type': 'list'},
                    'created_at': {
                        'required': False,
                        'type': 'datetime',
                        'unique': False},
                    'etag': {
                        'maxlength': 40,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'id': {
                        'required': False,
                        'type': 'string',
                        'unique': True},
                    'jobdefinition_components': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'jobdefinition_components'},
                        'type': 'objectid'},
                    'jobs': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'jobs'},
                        'type': 'objectid'},
                    'name': {
                        'maxlength': 200,
                        'nullable': True,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'test': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'tests'},
                        'type': 'objectid'},
                    'test_id': {
                        'data_relation': {
                            'embeddable': False,
                            'resource': 'tests'},
                        'required': True,
                        'type': 'objectid',
                        'unique': False},
                    'updated_at': {
                        'required': False,
                        'type': 'datetime',
                        'unique': False}}},
            'jobs': {
                'auth_field': 'team_id',
                'datasource': {
                    'default_sort': [('created_at', 1)],
                    'projection': {
                        'created_at': 1,
                        'etag': 1,
                        'id': 1,
                        'jobdefinition': 1,
                        'jobdefinition_id': 0,
                        'jobstates': 1,
                        'remoteci': 1,
                        'remoteci_id': 0,
                        'team': 1,
                        'team_id': 0,
                        'updated_at': 1},
                    'source': 'Job'},
                'description': {
                    'fields': {},
                    'general': 'A collection of components and a '
                    'test ready to associated to a '
                    'remoteci to create a new job.'},
                'id_field': 'id',
                'item_lookup': True,
                'item_lookup_field': 'id',
                'item_methods': ['PATCH', 'DELETE', 'PUT', 'GET'],
                'item_url': uuid_re,
                'public_item_methods': [],
                'public_methods': [],
                'resource_methods': ['GET', 'POST', 'DELETE'],
                'schema': {
                    'created_at': {
                        'required': False,
                        'type': 'datetime',
                        'unique': False},
                    'etag': {
                        'maxlength': 40,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'id': {
                        'required': False,
                        'type': 'string',
                        'unique': True},
                    'jobdefinition': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'jobdefinitions'},
                        'type': 'objectid'},
                    'jobdefinition_id': {
                        'data_relation': {
                            'embeddable': False,
                            'resource': 'jobdefinitions'},
                        'required': False,
                        'type': 'objectid',
                        'unique': False},
                    'jobstates': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'jobstates'},
                        'type': 'objectid'},
                    'remoteci': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'remotecis'},
                        'type': 'objectid'},
                    'remoteci_id': {
                        'data_relation': {
                            'embeddable': False,
                            'resource': 'remotecis'},
                        'required': True,
                        'type': 'objectid',
                        'unique': False},
                    'team': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'teams'},
                        'type': 'objectid'},
                    'team_id': {
                        'data_relation': {
                            'embeddable': False,
                            'resource': 'teams'},
                        'required': False,
                        'type': 'objectid',
                        'unique': False},
                    'updated_at': {
                        'required': False,
                        'type': 'datetime',
                        'unique': False}}},
            'jobstates': {
                'auth_field': 'team_id',
                'datasource': {
                    'default_sort': [('created_at', 1)],
                    'projection': {
                        'comment': 1,
                        'created_at': 1,
                        'etag': 1,
                        'files': 0,
                        'id': 1,
                        'job': 1,
                        'job_id': 0,
                        'jobs': 0,
                        'status': 1,
                        'team': 1,
                        'team_id': 0,
                        'updated_at': 1},
                    'source': 'Jobstate'},
                'description': {
                    'fields': {
                        'comment': 'ongoing: the job is '
                        'still running, '
                        'failure: the job '
                        'has failed and this '
                        'is the last status, '
                        'success: the job '
                        'has been run '
                        'successfully.'},
                    'general': 'One of the status during the '
                    'execution of a job. The last '
                    'one is the last know status.'},
                'id_field': 'id',
                'item_lookup': True,
                'item_lookup_field': 'id',
                'item_methods': ['PATCH', 'DELETE', 'PUT', 'GET'],
                'item_url': uuid_re,
                'public_item_methods': [],
                'public_methods': [],
                'resource_methods': ['GET', 'POST', 'DELETE'],
                'schema': {
                    'comment': {
                        'nullable': True,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'created_at': {
                        'required': False,
                        'type': 'datetime',
                        'unique': False},
                    'etag': {
                        'maxlength': 40,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'files': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'files'},
                        'type': 'objectid'},
                    'id': {
                        'required': False,
                        'type': 'string',
                        'unique': True},
                    'job': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'jobs'},
                        'type': 'objectid'},
                    'job_id': {
                        'data_relation': {
                            'embeddable': False,
                            'resource': 'jobs'},
                        'required': True,
                        'type': 'objectid',
                        'unique': False},
                    'status': {
                        'nullable': True,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'team': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'teams'},
                        'type': 'objectid'},
                    'team_id': {
                        'data_relation': {
                            'embeddable': False,
                            'resource': 'teams'},
                        'required': False,
                        'type': 'objectid',
                        'unique': False},
                    'updated_at': {
                        'required': False,
                        'type': 'datetime',
                        'unique': False}}},
            'remotecis': {
                'additional_lookup': {
                    'field': 'name',
                    'url': name_re},
                'auth_field': 'team_id',
                'datasource': {
                    'default_sort': [('created_at', 1)],
                    'projection': {
                        'created_at': 1,
                        'data': 1,
                        'etag': 1,
                        'id': 1,
                        'jobs': 0,
                        'name': 1,
                        'team': 1,
                        'team_id': 0,
                        'team': 1,
                        'test': 1,
                        'test_id': 0,
                        'updated_at': 1,
                        'user_remotecis': 0},
                    'source': 'Remoteci'},
                'description': {
                    'fields': {},
                    'general': 'The remote CI agent that '
                    'process the test.'},
                'id_field': 'id',
                'item_lookup': True,
                'item_lookup_field': 'id',
                'item_methods': ['PATCH', 'DELETE', 'PUT', 'GET'],
                'item_url': uuid_re,
                'public_item_methods': [],
                'public_methods': [],
                'resource_methods': ['GET', 'POST', 'DELETE'],
                'schema': {
                    'created_at': {
                        'required': False,
                        'type': 'datetime',
                        'unique': False},
                    'data': {
                        'nullable': True,
                        'required': False,
                        'type': 'json',
                        'unique': False},
                    'etag': {
                        'maxlength': 40,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'id': {
                        'required': False,
                        'type': 'string',
                        'unique': True},
                    'jobs': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'jobs'},
                        'type': 'objectid'},
                    'name': {
                        'maxlength': 255,
                        'nullable': True,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'team': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'teams'},
                        'type': 'objectid'},
                    'team_id': {
                        'data_relation': {
                            'embeddable': False,
                            'resource': 'teams'},
                        'required': False,
                        'type': 'objectid',
                        'unique': False},
                    'test': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'tests'},
                        'type': 'objectid'},
                    'test_id': {
                        'data_relation': {
                            'embeddable': False,
                            'resource': 'tests'},
                        'required': True,
                        'type': 'objectid',
                        'unique': False},
                    'updated_at': {
                        'required': False,
                        'type': 'datetime',
                        'unique': False},
                    'user_remotecis': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'user_remotecis'},
                        'type': 'objectid'}}},
            'roles': {
                'additional_lookup': {
                    'field': 'name',
                    'url': name_re},
                'datasource': {
                    'default_sort': [('created_at', 1)],
                    'projection': {
                        'created_at': 1,
                        'etag': 1,
                        'id': 1,
                        'name': 1,
                        'updated_at': 1,
                        'user_roles': 0},
                    'source': 'Role'},
                'description': {
                    'fields': {}, 'general': 'The user roles.'},
                'id_field': 'id',
                'item_lookup': True,
                'item_lookup_field': 'id',
                'item_methods': ['PATCH', 'DELETE', 'PUT', 'GET'],
                'item_url': uuid_re,
                'public_item_methods': [],
                'public_methods': [],
                'resource_methods': ['GET', 'POST', 'DELETE'],
                'schema': {
                    'created_at': {
                        'required': False,
                        'type': 'datetime',
                        'unique': False},
                    'etag': {
                        'maxlength': 40,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'id': {
                        'required': False,
                        'type': 'string',
                        'unique': True},
                    'name': {
                        'maxlength': 100,
                        'nullable': True,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'updated_at': {
                        'required': False,
                        'type': 'datetime',
                        'unique': False},
                    'user_roles': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'user_roles'},
                        'type': 'objectid'}}},
            'teams': {
                'additional_lookup': {
                    'field': 'name',
                    'url': name_re},
                'datasource': {
                    'default_sort': [('created_at', 1)],
                    'projection': {
                        'created_at': 1,
                        'etag': 1,
                        'files': 0,
                        'id': 1,
                        'jobs': 0,
                        'name': 1,
                        'remotecis': 1,
                        'updated_at': 1,
                        'users': 0},
                    'source': 'Team'},
                'description': {
                    'fields': {},
                    'general': 'The user team. An user can only be '
                    'in one team. All the resource '
                    'created by an user are shared with '
                    'his/her team members.'},
                'id_field': 'id',
                'item_lookup': True,
                'item_lookup_field': 'id',
                'item_methods': ['PATCH', 'DELETE', 'PUT', 'GET'],
                'item_url': uuid_re,
                'public_item_methods': [],
                'public_methods': [],
                'resource_methods': ['GET', 'POST', 'DELETE'],
                'schema': {
                    'created_at': {
                        'required': False,
                        'type': 'datetime',
                        'unique': False},
                    'etag': {
                        'maxlength': 40,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'files': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'files'},
                        'type': 'objectid'},
                    'id': {
                        'required': False,
                        'type': 'string',
                        'unique': True},
                    'jobs': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'jobs'},
                        'type': 'objectid'},
                    'name': {
                        'maxlength': 100,
                        'nullable': True,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'remotecis': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'remotecis'},
                        'type': 'objectid'},
                    'updated_at': {
                        'required': False,
                        'type': 'datetime',
                        'unique': False},
                    'users': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'users'},
                        'type': 'objectid'}}},
            'tests': {
                'additional_lookup': {
                    'field': 'name',
                    'url': name_re},
                'datasource': {
                    'default_sort': [('created_at', 1)],
                    'projection': {
                        'created_at': 1,
                        'data': 1,
                        'etag': 1,
                        'id': 1,
                        'jobdefinitions': 0,
                        'name': 1,
                        'remotecis': 0,
                        'updated_at': 1},
                    'source': 'Test'},
                'description': {
                    'fields': {}, 'general': 'A QA test.'},
                'id_field': 'id',
                'item_lookup': True,
                'item_lookup_field': 'id',
                'item_methods': ['PATCH', 'DELETE', 'PUT', 'GET'],
                'item_url': uuid_re,
                'public_item_methods': [],
                'public_methods': [],
                'resource_methods': ['GET', 'POST', 'DELETE'],
                'schema': {
                    'created_at': {
                        'required': False,
                        'type': 'datetime',
                        'unique': False},
                    'data': {
                        'nullable': True,
                        'required': False,
                        'type': 'json',
                        'unique': False},
                    'etag': {
                        'maxlength': 40,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'id': {
                        'required': False,
                        'type': 'string',
                        'unique': True},
                    'jobdefinitions': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'jobdefinitions'},
                        'type': 'objectid'},
                    'name': {
                        'maxlength': 255,
                        'required': True,
                        'type': 'string',
                        'unique': False},
                    'remotecis': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'remotecis'},
                        'type': 'objectid'},
                    'updated_at': {
                        'required': False,
                        'type': 'datetime',
                        'unique': False}}},
            'user_remotecis': {
                'datasource': {
                    'default_sort': [('created_at', 1)],
                    'projection': {
                        'created_at': 1,
                        'etag': 1,
                        'id': 1,
                        'remoteci': 1,
                        'remoteci_id': 0,
                        'updated_at': 0,
                        'user': 1,
                        'user_id': 0,
                        'users': 0},
                    'source': 'UserRemoteci'},
                'description': {
                    'fields': {}, 'general': 'experimental'},
                'id_field': 'id',
                'item_lookup': True,
                'item_lookup_field': 'id',
                'item_methods': ['PATCH', 'DELETE', 'PUT', 'GET'],
                'item_url': uuid_re,
                'public_item_methods': [],
                'public_methods': [],
                'resource_methods': ['GET', 'POST', 'DELETE'],
                'schema': {
                    'created_at': {
                        'required': False,
                        'type': 'datetime',
                        'unique': False},
                    'etag': {
                        'maxlength': 40,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'id': {
                        'required': False,
                        'type': 'string',
                        'unique': True},
                    'remoteci': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'remotecis'},
                        'type': 'objectid'},
                    'remoteci_id': {
                        'data_relation': {
                            'embeddable': False,
                            'resource': 'remotecis'},
                        'required': True,
                        'type': 'objectid',
                        'unique': False},
                    'updated_at': {
                        'required': False,
                        'type': 'datetime',
                        'unique': False},
                    'user': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'users'},
                        'type': 'objectid'},
                    'user_id': {
                        'data_relation': {
                            'embeddable': False,
                            'resource': 'users'},
                        'required': True,
                        'type': 'objectid',
                        'unique': False}}},
            'user_roles': {
                'datasource': {
                    'default_sort': [('created_at', 1)],
                    'projection': {
                        'created_at': 1,
                        'etag': 1,
                        'id': 1,
                        'role': 1,
                        'role_id': 0,
                        'roles': 0,
                        'updated_at': 1,
                        'user': 1,
                        'user_id': 0,
                        'users': 0},
                    'source': 'UserRole'},
                'description': {
                    'fields': {},
                    'general': 'Relation table between the '
                    'users and the roles.'},
                'id_field': 'id',
                'item_lookup': True,
                'item_lookup_field': 'id',
                'item_methods': ['PATCH', 'DELETE', 'PUT', 'GET'],
                'item_url': uuid_re,
                'public_item_methods': [],
                'public_methods': [],
                'resource_methods': ['GET', 'POST', 'DELETE'],
                'schema': {
                    'created_at': {
                        'required': False,
                        'type': 'datetime',
                        'unique': False},
                    'etag': {
                        'maxlength': 40,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'id': {
                        'required': False,
                        'type': 'string',
                        'unique': True},
                    'role': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'roles'},
                        'type': 'objectid'},
                    'role_id': {
                        'data_relation': {
                            'embeddable': False,
                            'resource': 'roles'},
                        'required': True,
                        'type': 'objectid',
                        'unique': False},
                    'updated_at': {
                        'required': False,
                        'type': 'datetime',
                        'unique': False},
                    'user': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'users'},
                        'type': 'objectid'},
                    'user_id': {
                        'data_relation': {
                            'embeddable': False,
                            'resource': 'users'},
                        'required': True,
                        'type': 'objectid',
                        'unique': False}}},
            'users': {
                'additional_lookup': {
                    'field': 'name',
                    'url': name_re},
                'auth_field': 'team_id',
                'datasource': {
                    'default_sort': [('created_at', 1)],
                    'projection': {
                        'created_at': 1,
                        'etag': 1,
                        'id': 1,
                        'name': 1,
                        'password': 1,
                        'team': 1,
                        'team_id': 0,
                        'updated_at': 1,
                        'user_remotecis': 0,
                        'user_roles': 0,
                        'roles': 1},
                    'source': 'User'},
                'description': {
                    'fields': {}, 'general': 'The user list.'},
                'id_field': 'id',
                'item_lookup': True,
                'item_lookup_field': 'id',
                'item_methods': ['PATCH', 'DELETE', 'PUT', 'GET'],
                'item_url': uuid_re,
                'public_item_methods': [],
                'public_methods': [],
                'resource_methods': ['GET', 'POST', 'DELETE'],
                'schema': {
                    'created_at': {
                        'required': False,
                        'type': 'datetime',
                        'unique': False},
                    'etag': {
                        'maxlength': 40,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'id': {
                        'required': False,
                        'type': 'string',
                        'unique': True},
                    'name': {
                        'maxlength': 100,
                        'nullable': True,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'password': {
                        'nullable': True,
                        'required': False,
                        'type': 'string',
                        'unique': False},
                    'team': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'teams'},
                        'type': 'objectid'},
                    'team_id': {
                        'data_relation': {
                            'embeddable': False,
                            'resource': 'teams'},
                        'required': False,
                        'type': 'objectid',
                        'unique': False},
                    'teams': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'teams'},
                        'type': 'objectid'},
                    'updated_at': {
                        'required': False,
                        'type': 'datetime',
                        'unique': False},
                    'user_remotecis': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'user_remotecis'},
                        'type': 'objectid'},
                    'user_roles': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'user_roles'},
                        'type': 'objectid'},
                    'roles': {
                        'data_relation': {
                            'embeddable': True,
                            'resource': 'roles'},
                        'type': 'objectid'}}}}
        return domain
