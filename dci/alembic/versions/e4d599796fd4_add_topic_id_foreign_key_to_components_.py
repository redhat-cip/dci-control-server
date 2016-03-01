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

from dci.common import utils
from dci.db import models

import datetime


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
    db_conn.execute(models.TOPICS.insert().values(**topic_values))

    # Adds all components, jobdefinitions and tests to the default topics
    values = {'topic_id': topic_id}
    db_conn.execute(models.COMPONENTS.update().values(**values))
    db_conn.execute(models.JOBDEFINITIONS.update().values(**values))
    db_conn.execute(models.TESTS.update().values(**values))

    # Adds all teams to the default topics
    all_teams = db_conn.execute(models.TEAMS.select()).fetchall()

    teams_topic = [{'topic_id': topic_id, 'team_id': team['id']}
                   for team in all_teams]
    if teams_topic:
        db_conn.execute(models.JOINS_TOPICS_TEAMS.insert(), teams_topic)


def downgrade():
    """Not supported at this time, will be implemented later"""
