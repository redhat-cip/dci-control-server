# -*- coding: utf-8 -*-
#
# Copyright (C) Red Hat, Inc
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

from dci.common import signature
from dci.db import declarative as dci_declarative

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm as sa_orm
import sqlalchemy_utils as sa_utils

Base = declarative_base()

JOB_STATUSES = ['new', 'pre-run', 'running', 'post-run',
                'success', 'failure', 'killed', 'error']
STATUSES = sa.Enum(*JOB_STATUSES, name='statuses')
FINAL_STATUSES = ['success', 'failure', 'error']
FINAL_FAILURE_STATUSES = ['failure', 'error']
FINAL_STATUSES_ENUM = sa.Enum(*FINAL_STATUSES, name='final_statuses')

RESOURCE_STATES = ['active', 'inactive', 'archived']
STATES = sa.Enum(*RESOURCE_STATES, name='states')

ISSUE_TRACKERS = ['github', 'bugzilla']
TRACKERS = sa.Enum(*ISSUE_TRACKERS, name='trackers')


USERS_TEAMS = sa.Table(
    'users_teams', Base.metadata,
    sa.Column('user_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('users.id', ondelete='CASCADE'),
              nullable=False),
    sa.Column('team_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('teams.id', ondelete='CASCADE'),
              nullable=True),
    sa.UniqueConstraint('user_id', 'team_id', name='users_teams_key')
)

USER_REMOTECIS = sa.Table(
    'user_remotecis', Base.metadata,
    sa.Column('user_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('users.id', ondelete='CASCADE'),
              nullable=False, primary_key=True),
    sa.Column('remoteci_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('remotecis.id', ondelete='CASCADE'),
              nullable=False, primary_key=True)
)


class User(dci_declarative.Mixin, Base):
    __tablename__ = 'users'

    name = sa.Column(sa.String(255), nullable=False, unique=True)
    sso_username = sa.Column(sa.String(255), nullable=True, unique=True)
    fullname = sa.Column(sa.String(255), nullable=False)
    email = sa.Column(sa.String(255), nullable=False, unique=True)
    password = sa.Column(sa.Text, nullable=True)
    timezone = sa.Column(sa.String(255), nullable=False, default='UTC')
    state = sa.Column(STATES, default='active')
    team = sa_orm.relationship('Team', secondary=USERS_TEAMS, back_populates='users')
    remotecis = sa_orm.relationship('Remoteci', secondary=USER_REMOTECIS, back_populates='users')

    def serialize(self, ignore_columns=[]):
        ignore_columns = list(ignore_columns)
        if 'password' not in ignore_columns:
            ignore_columns.append('password')
        return super(User, self).serialize(ignore_columns=ignore_columns)


JOINS_TOPICS_TEAMS = sa.Table(
    'topics_teams', Base.metadata,
    sa.Column('topic_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('topics.id', ondelete='CASCADE'),
              nullable=False, primary_key=True),
    sa.Column('team_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('teams.id', ondelete='CASCADE'),
              nullable=False, primary_key=True)
)


class Team(dci_declarative.Mixin, Base):
    __tablename__ = 'teams'
    __table_args__ = (sa.UniqueConstraint('name', name='teams_name_key'),)

    name = sa.Column(sa.String(255), nullable=False)
    # https://en.wikipedia.org/wiki/ISO_3166-1 Alpha-2 code
    country = sa.Column(sa.String(255), nullable=True)
    state = sa.Column(STATES, default='active')
    external = sa.Column(sa.BOOLEAN, default=True)
    users = sa_orm.relationship('User', secondary=USERS_TEAMS, back_populates='team')
    remotecis = sa_orm.relationship('Remoteci')
    topics = sa_orm.relationship('Topic', secondary=JOINS_TOPICS_TEAMS, back_populates='teams')


class Topic(dci_declarative.Mixin, Base):
    __tablename__ = 'topics'
    __table_args__ = (sa.Index('topics_product_id_idx', 'product_id'),
                      sa.Index('topics_next_topic_id_idx', 'next_topic_id'))

    name = sa.Column('name', sa.String(255), unique=True, nullable=False)
    component_types = sa.Column('component_types', pg.JSON, default=[])
    product_id = sa.Column('product_id', pg.UUID(as_uuid=True), sa.ForeignKey('products.id'), nullable=True)
    next_topic_id = sa.Column('next_topic_id', pg.UUID(as_uuid=True), sa.ForeignKey('topics.id'), nullable=True, default=None)
    export_control = sa.Column('export_control', sa.BOOLEAN, nullable=False, default=False, server_default='false')
    state = sa.Column('state', STATES, default='active')
    data = sa.Column('data', sa_utils.JSONType, default={})
    teams = sa_orm.relationship('Team', secondary=JOINS_TOPICS_TEAMS, back_populates='topics')


class Remoteci(dci_declarative.Mixin, Base):
    __tablename__ = 'remotecis'
    __table_args__ = (sa.Index('remotecis_team_id_idx', 'team_id'),
                      sa.UniqueConstraint('name', 'team_id', name='remotecis_name_team_id_key'))

    name = sa.Column('name', sa.String(255))
    data = sa.Column('data', sa_utils.JSONType)
    api_secret = sa.Column('api_secret', sa.String(64), default=signature.gen_secret)
    team_id = sa.Column('team_id', pg.UUID(as_uuid=True), sa.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False)
    public = sa.Column('public', sa.BOOLEAN, default=False)
    cert_fp = sa.Column('cert_fp', sa.String(255))
    state = sa.Column('state', STATES, default='active')
    users = sa_orm.relationship('User', secondary=USER_REMOTECIS, back_populates='remotecis')


class Product(dci_declarative.Mixin, Base):
    __tablename__ = 'products'
