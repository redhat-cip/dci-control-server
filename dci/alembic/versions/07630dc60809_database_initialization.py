#
# Copyright (C) 2016 Red Hat, Inc
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

"""Database initialization

Revision ID: 07630dc60809
Revises:
Create Date: 2016-01-15 09:19:34.996037

"""

# revision identifiers, used by Alembic.
revision = '07630dc60809'
down_revision = None
branch_labels = None
depends_on = None

import datetime

import alembic.op as op
import sqlalchemy as sa
import sqlalchemy_utils as sa_utils

import dci.common.utils as utils


def upgrade():
    op.create_table(
        'components',
        sa.Column('id', sa.String(36), primary_key=True,
                  default=utils.gen_uuid),
        sa.Column('created_at', sa.DateTime(),
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('updated_at', sa.DateTime(),
                  onupdate=datetime.datetime.utcnow,
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('etag', sa.String(40), nullable=False,
                  default=utils.gen_etag, onupdate=utils.gen_etag),
        sa.Column('name', sa.String(255), unique=True, nullable=False),
        sa.Column('type', sa.String(255), nullable=False),
        sa.Column('canonical_project_name', sa.String),
        sa.Column('data', sa_utils.JSONType),
        sa.Column('sha', sa.Text),
        sa.Column('title', sa.Text),
        sa.Column('message', sa.Text),
        sa.Column('url', sa.Text),
        sa.Column('git', sa.Text),
        sa.Column('ref', sa.Text)
    )

    op.create_table(
        'tests',
        sa.Column('id', sa.String(36), primary_key=True,
                  default=utils.gen_uuid),
        sa.Column('created_at', sa.DateTime(),
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('updated_at', sa.DateTime(),
                  onupdate=datetime.datetime.utcnow,
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('etag', sa.String(40), nullable=False,
                  default=utils.gen_etag, onupdate=utils.gen_etag),
        sa.Column('data', sa_utils.JSONType)
    )

    op.create_table(
        'jobdefinitions',
        sa.Column('id', sa.String(36), primary_key=True,
                  default=utils.gen_uuid),
        sa.Column('created_at', sa.DateTime(),
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('updated_at', sa.DateTime(),
                  onupdate=datetime.datetime.utcnow,
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('etag', sa.String(40), nullable=False,
                  default=utils.gen_etag, onupdate=utils.gen_etag),
        sa.Column('name', sa.String(255)),
        sa.Column('priority', sa.Integer, default=0),
        sa.Column('test_id', sa.String(36),
                  sa.ForeignKey('tests.id', ondelete="CASCADE"),
                  nullable=False)
    )

    op.create_table(
        'jobdefinition_components',
        sa.Column('id', sa.String(36), primary_key=True,
                  default=utils.gen_uuid),
        sa.Column('created_at', sa.DateTime(),
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('updated_at', sa.DateTime(),
                  onupdate=datetime.datetime.utcnow,
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('etag', sa.String(40), nullable=False,
                  default=utils.gen_etag, onupdate=utils.gen_etag),
        sa.Column('component_id', sa.String(36),
                  sa.ForeignKey('components.id', ondelete="CASCADE"),
                  nullable=False),
        sa.Column('jobdefinition_id', sa.String(36),
                  sa.ForeignKey('jobdefinitions.id', ondelete="CASCADE"),
                  nullable=False),
        sa.UniqueConstraint('component_id', 'jobdefinition_id')
    )

    op.create_table(
        'teams',
        sa.Column('id', sa.String(36), primary_key=True,
                  default=utils.gen_uuid),
        sa.Column('created_at', sa.DateTime(),
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('updated_at', sa.DateTime(),
                  onupdate=datetime.datetime.utcnow,
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('etag', sa.String(40), nullable=False,
                  default=utils.gen_etag, onupdate=utils.gen_etag),
        sa.Column('name', sa.String(255), unique=True, nullable=False)
    )

    op.create_table(
        'remotecis',
        sa.Column('id', sa.String(36), primary_key=True,
                  default=utils.gen_uuid),
        sa.Column('created_at', sa.DateTime(),
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('updated_at', sa.DateTime(),
                  onupdate=datetime.datetime.utcnow,
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('etag', sa.String(40), nullable=False,
                  default=utils.gen_etag, onupdate=utils.gen_etag),
        sa.Column('name', sa.String(255), unique=True),
        sa.Column('data', sa_utils.JSONType),
        sa.Column('active', sa.BOOLEAN, default=True),
        sa.Column('team_id', sa.String(36),
                  sa.ForeignKey('teams.id', ondelete="CASCADE"),
                  nullable=False)
    )

    op.create_table(
        'jobs',
        sa.Column('id', sa.String(36), primary_key=True,
                  default=utils.gen_uuid),
        sa.Column('created_at', sa.DateTime(),
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('updated_at', sa.DateTime(),
                  onupdate=datetime.datetime.utcnow,
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('etag', sa.String(40), nullable=False,
                  default=utils.gen_etag, onupdate=utils.gen_etag),
        sa.Column('recheck', sa.Boolean, default=False),
        # new, pre-run, running, post-run, success, failure
        sa.Column('status', sa.String(255), default='new'),
        sa.Column('jobdefinition_id', sa.String(36),
                  sa.ForeignKey('jobdefinitions.id', ondelete="CASCADE"),
                  nullable=False),
        sa.Column('remoteci_id', sa.String(36),
                  sa.ForeignKey('remotecis.id', ondelete="CASCADE"),
                  nullable=False),
        sa.Column('team_id', sa.String(36),
                  sa.ForeignKey('teams.id', ondelete="CASCADE"),
                  nullable=False)
    )

    op.create_table(
        'jobstates',
        sa.Column('id', sa.String(36), primary_key=True,
                  default=utils.gen_uuid),
        sa.Column('created_at', sa.DateTime(),
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('updated_at', sa.DateTime(),
                  onupdate=datetime.datetime.utcnow,
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('etag', sa.String(40), nullable=False,
                  default=utils.gen_etag, onupdate=utils.gen_etag),
        # new, pre-run, running, post-run, success, failure
        sa.Column('status', sa.String(255), nullable=False),
        sa.Column('comment', sa.Text),
        sa.Column('job_id', sa.String(36),
                  sa.ForeignKey('jobs.id', ondelete="CASCADE"),
                  nullable=False),
        sa.Column('team_id', sa.String(36),
                  sa.ForeignKey('teams.id', ondelete="CASCADE"),
                  nullable=False)
    )

    op.create_table(
        'files',
        sa.Column('id', sa.String(36), primary_key=True,
                  default=utils.gen_uuid),
        sa.Column('created_at', sa.DateTime(),
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('updated_at', sa.DateTime(),
                  onupdate=datetime.datetime.utcnow,
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('etag', sa.String(40), nullable=False,
                  default=utils.gen_etag, onupdate=utils.gen_etag),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('mime', sa.String),
        sa.Column('md5', sa.String(32)),
        sa.Column('jobstate_id', sa.String(36),
                  sa.ForeignKey('jobstates.id', ondelete="CASCADE"),
                  nullable=False),
        sa.Column('team_id', sa.String(36),
                  sa.ForeignKey('teams.id', ondelete="CASCADE"),
                  nullable=False)
    )

    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True,
                  default=utils.gen_uuid),
        sa.Column('created_at', sa.DateTime(),
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('updated_at', sa.DateTime(),
                  onupdate=datetime.datetime.utcnow,
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('etag', sa.String(40), nullable=False,
                  default=utils.gen_etag, onupdate=utils.gen_etag),
        sa.Column('name', sa.String(255), unique=True, nullable=False),
        sa.Column('password', sa.Text, nullable=False),
        sa.Column('role', sa.String(255), default='user', nullable=False),
        sa.Column('team_id', sa.String(36),
                  sa.ForeignKey('teams.id', ondelete="CASCADE"),
                  nullable=False)
    )

    op.create_table(
        'user_remotecis',
        sa.Column('id', sa.String(36), primary_key=True,
                  default=utils.gen_uuid),
        sa.Column('created_at', sa.DateTime(),
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('updated_at', sa.DateTime(),
                  onupdate=datetime.datetime.utcnow,
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('etag', sa.String(40), nullable=False,
                  default=utils.gen_etag, onupdate=utils.gen_etag),
        sa.Column('user_id', sa.String(36),
                  sa.ForeignKey('users.id', ondelete="CASCADE"),
                  nullable=False),
        sa.Column('remoteci_id', sa.String(36),
                  sa.ForeignKey('remotecis.id', ondelete="CASCADE"),
                  nullable=False),
        sa.UniqueConstraint('user_id', 'remoteci_id')
    )


def downgrade():
    pass
