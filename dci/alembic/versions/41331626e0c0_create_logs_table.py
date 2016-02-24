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

"""create logs table

Revision ID: 41331626e0c0
Revises: c92c843fc800
Create Date: 2016-02-23 09:26:57.004419

"""

# revision identifiers, used by Alembic.
revision = '41331626e0c0'
down_revision = 'c92c843fc800'
branch_labels = None
depends_on = None

import datetime

from alembic import op
import sqlalchemy as sa

import dci.common.utils as utils


def upgrade():
    op.create_table(
        'logs',
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
        sa.Column('action', sa.Text, nullable=False)
    )


def downgrade():
    pass
