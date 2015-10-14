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
from sqlalchemy.types import Boolean
from sqlalchemy.types import DateTime
from sqlalchemy.types import Integer
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
        priority = Column(Integer())
        test_id = Column(UUID(), ForeignKey('tests.id'))
        test = relationship('Test', uselist=False)

    class Job(DCIBase):
        __tablename__ = 'jobs'
        recheck = Column(Boolean())
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
