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

"""Add topics and topics_teams tables.

Revision ID: 1e21b8c3f464
Revises: c92c843fc800
Create Date: 2016-02-17 16:47:17.012410

"""

# revision identifiers, used by Alembic.
revision = '1e21b8c3f464'
down_revision = 'a199a93a0bc6'
branch_labels = None
depends_on = None

import datetime

from alembic import op
import sqlalchemy as sa

import dci.common.utils as utils


def upgrade():
    op.create_table(
        'topics',
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
        'topics_teams',
        sa.Column('topic_id', sa.String(36),
                  sa.ForeignKey('topics.id', ondelete="CASCADE"),
                  nullable=False, primary_key=True),
        sa.Column('team_id', sa.String(36),
                  sa.ForeignKey('teams.id', ondelete="CASCADE"),
                  nullable=False, primary_key=True)
    )


def downgrade():
    """Not supported at this time, will be implemented later"""
