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

"""Add topic_id foreign key to components, jobdefinition and tests.

Revision ID: e4d599796fd4
Revises: 1e21b8c3f464
Create Date: 2016-02-18 11:43:43.804876

"""

# revision identifiers, used by Alembic.
revision = 'e4d599796fd4'
down_revision = '1e21b8c3f464'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
import sqlalchemy_utils as sa_utils

from dci.common import utils
from dci.db import models

import datetime

COMPONENTS = sa.Table(
    'components', sa.MetaData(),
    sa.Column('id', sa.String(36), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
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
              sa.ForeignKey('topics.id', ondelete='CASCADE'),
              nullable=True),
    sa.UniqueConstraint('name', 'topic_id',
                        name='components_name_topic_id_key'))

TEAMS = sa.Table(
    'teams', sa.MetaData(),
    sa.Column('id', sa.String(36), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
    sa.Column('name', sa.String(255), unique=True, nullable=False),
)


TESTS = sa.Table(
    'tests', sa.MetaData(),
    sa.Column('id', sa.String(36), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('name', sa.String(255), nullable=False, unique=True),
    sa.Column('data', sa_utils.JSONType),
    sa.Column('topic_id', sa.String(36),
              sa.ForeignKey('topics.id', ondelete='CASCADE'),
              nullable=True))


TOPICS = sa.Table(
    'topics', sa.MetaData(),
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

JOBDEFINITIONS = sa.Table(
    'jobdefinitions', sa.MetaData(),
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
    sa.Column('name', sa.String(255)),
    sa.Column('topic_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('topics.id', ondelete='CASCADE'),
              nullable=True),
    sa.Index('jobdefinitions_topic_id_idx', 'topic_id'),
    sa.Column('comment', sa.Text),
    sa.Column('component_types', pg.JSON, default=[]),
)


def upgrade():
    op.add_column('components',
                  sa.Column('topic_id', sa.String(36),
                            sa.ForeignKey('topics.id', ondelete="CASCADE"),
                            nullable=True))
    op.add_column('tests',
                  sa.Column('topic_id', sa.String(36),
                            sa.ForeignKey('topics.id', ondelete="CASCADE"),
                            nullable=True))
    op.add_column('jobdefinitions',
                  sa.Column('topic_id', sa.String(36),
                            sa.ForeignKey('topics.id', ondelete="CASCADE"),
                            nullable=True))
    db_conn = op.get_bind()

    # Create a default topic
    topic_id = utils.gen_uuid()
    topic_values = {
        'id': topic_id,
        'created_at': datetime.datetime.utcnow().isoformat(),
        'updated_at': datetime.datetime.utcnow().isoformat(),
        'etag': utils.gen_etag(),
        'name': 'default'
    }
    db_conn.execute(TOPICS.insert().values(**topic_values))

    # Adds all components, jobdefinitions and tests to the default topics
    values = {'topic_id': topic_id}
    db_conn.execute(COMPONENTS.update().values(**values))
    db_conn.execute(JOBDEFINITIONS.update().values(**values))
    db_conn.execute(TESTS.update().values(**values))

    # Adds all teams to the default topics
    all_teams = db_conn.execute(TEAMS.select()).fetchall()

    teams_topic = [{'topic_id': topic_id, 'team_id': team['id']}
                   for team in all_teams]
    if teams_topic:
        db_conn.execute(models.JOINS_TOPICS_TEAMS.insert(), teams_topic)


def downgrade():
    """Not supported at this time, will be implemented later"""
