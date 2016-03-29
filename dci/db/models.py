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

import sqlalchemy as sa
import sqlalchemy_utils as sa_utils

from dci.common import utils

metadata = sa.MetaData()

USER_ROLES = ['user', 'admin']
ROLES = sa.Enum(*USER_ROLES, name='roles')

JOB_STATUSES = ['new', 'pre-run', 'running', 'post-run', 'success', 'failure']
STATUSES = sa.Enum(*JOB_STATUSES, name='statuses')

COMPONENTS = sa.Table(
    'components', metadata,
    sa.Column('id', sa.String(36), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('name', sa.String(255), nullable=False),
    sa.Column('type', sa.String(255), nullable=False),
    sa.Column('canonical_project_name', sa.String),
    sa.Column('data', sa_utils.JSONType),
    sa.Column('sha', sa.Text),
    sa.Column('title', sa.Text),
    sa.Column('message', sa.Text),
    sa.Column('url', sa.Text),
    sa.Column('git', sa.Text),
    sa.Column('ref', sa.Text),
    sa.Column('topic_id', sa.String(36),
              sa.ForeignKey('topics.id', ondelete="CASCADE"),
              nullable=True),
    sa.UniqueConstraint('name', 'topic_id',
                        name='components_name_topic_id_key'))


TOPICS = sa.Table(
    'topics', metadata,
    sa.Column('id', sa.String(36), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
    sa.Column('name', sa.String(255), unique=True, nullable=False)
)

JOINS_TOPICS_TEAMS = sa.Table(
    'topics_teams', metadata,
    sa.Column('topic_id', sa.String(36),
              sa.ForeignKey('topics.id', ondelete="CASCADE"),
              nullable=False, primary_key=True),
    sa.Column('team_id', sa.String(36),
              sa.ForeignKey('teams.id', ondelete="CASCADE"),
              nullable=False, primary_key=True)
)

TESTS = sa.Table(
    'tests', metadata,
    sa.Column('id', sa.String(36), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('name', sa.String(255), nullable=False, unique=True),
    sa.Column('data', sa_utils.JSONType),
    sa.Column('topic_id', sa.String(36),
              sa.ForeignKey('topics.id', ondelete="CASCADE"),
              nullable=True))

JOBDEFINITIONS = sa.Table(
    'jobdefinitions', metadata,
    sa.Column('id', sa.String(36), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
    sa.Column('name', sa.String(255)),
    sa.Column('priority', sa.Integer, default=0),
    sa.Column('test_id', sa.String(36),
              sa.ForeignKey('tests.id', ondelete="CASCADE"),
              nullable=False),
    sa.Column('topic_id', sa.String(36),
              sa.ForeignKey('topics.id', ondelete="CASCADE"),
              nullable=True),
    sa.Column('active', sa.BOOLEAN, default=True),
    sa.Column('comment', sa.Text),
)

JOIN_JOBDEFINITIONS_COMPONENTS = sa.Table(
    'jobdefinition_components', metadata,
    sa.Column('component_id', sa.String(36),
              sa.ForeignKey('components.id', ondelete="CASCADE"),
              nullable=False, primary_key=True),
    sa.Column('jobdefinition_id', sa.String(36),
              sa.ForeignKey('jobdefinitions.id', ondelete="CASCADE"),
              nullable=False, primary_key=True)
)

TEAMS = sa.Table(
    'teams', metadata,
    sa.Column('id', sa.String(36), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
    sa.Column('name', sa.String(255), unique=True, nullable=False))

REMOTECIS = sa.Table(
    'remotecis', metadata,
    sa.Column('id', sa.String(36), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
    sa.Column('name', sa.String(255)),
    sa.Column('data', sa_utils.JSONType),
    sa.Column('active', sa.BOOLEAN, default=True),
    sa.Column('team_id', sa.String(36),
              sa.ForeignKey('teams.id', ondelete="CASCADE"),
              nullable=False),
    sa.UniqueConstraint('name', 'team_id', name='remotecis_name_team_id_key')
)

JOBS = sa.Table(
    'jobs', metadata,
    sa.Column('id', sa.String(36), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
    sa.Column('comment', sa.Text),
    sa.Column('recheck', sa.Boolean, default=False),
    sa.Column('status', STATUSES, default='new'),
    sa.Column('jobdefinition_id', sa.String(36),
              sa.ForeignKey('jobdefinitions.id', ondelete="CASCADE"),
              nullable=False),
    sa.Column('remoteci_id', sa.String(36),
              sa.ForeignKey('remotecis.id', ondelete="CASCADE"),
              nullable=False),
    sa.Column('team_id', sa.String(36),
              sa.ForeignKey('teams.id', ondelete="CASCADE"),
              nullable=False))

JOBSTATES = sa.Table(
    'jobstates', metadata,
    sa.Column('id', sa.String(36), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('status', STATUSES, nullable=False),
    sa.Column('comment', sa.Text),
    sa.Column('job_id', sa.String(36),
              sa.ForeignKey('jobs.id', ondelete="CASCADE"),
              nullable=False),
    sa.Column('team_id', sa.String(36),
              sa.ForeignKey('teams.id', ondelete="CASCADE"),
              nullable=False))

FILES = sa.Table(
    'files', metadata,
    sa.Column('id', sa.String(36), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('name', sa.String(255), nullable=False),
    sa.Column('content', sa.Text, nullable=False),
    sa.Column('mime', sa.String),
    sa.Column('md5', sa.String(32)),
    sa.Column('jobstate_id', sa.String(36),
              sa.ForeignKey('jobstates.id', ondelete="CASCADE"),
              nullable=True),
    sa.Column('team_id', sa.String(36),
              sa.ForeignKey('teams.id', ondelete="CASCADE"),
              nullable=False),
    sa.Column('job_id', sa.String(36),
              sa.ForeignKey('jobs.id', ondelete="CASCADE"),
              nullable=True))

USERS = sa.Table(
    'users', metadata,
    sa.Column('id', sa.String(36), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
    sa.Column('name', sa.String(255), nullable=False, unique=True),
    sa.Column('password', sa.Text, nullable=False),
    sa.Column('role', ROLES, default=USER_ROLES[0], nullable=False),
    sa.Column('team_id', sa.String(36),
              sa.ForeignKey('teams.id', ondelete="CASCADE"),
              nullable=False))

JOIN_USER_REMOTECIS = sa.Table(
    'user_remotecis', metadata,
    sa.Column('user_id', sa.String(36),
              sa.ForeignKey('users.id', ondelete="CASCADE"),
              nullable=False, primary_key=True),
    sa.Column('remoteci_id', sa.String(36),
              sa.ForeignKey('remotecis.id', ondelete="CASCADE"),
              nullable=False, primary_key=True)
)

LOGS = sa.Table(
    'logs', metadata,
    sa.Column('id', sa.String(36), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('user_id', sa.String(36),
              sa.ForeignKey('users.id', ondelete="CASCADE"),
              nullable=False),
    sa.Column('team_id', sa.String(36),
              sa.ForeignKey('teams.id', ondelete="CASCADE"),
              nullable=False),
    sa.Column('action', sa.Text, nullable=False))
