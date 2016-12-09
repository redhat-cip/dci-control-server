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

"""Add upgrade fields.

Revision ID: 82f4f4d14775
Revises: c804329ffeda
Create Date: 2016-12-09 16:51:44.546909

"""

# revision identifiers, used by Alembic.
revision = '82f4f4d14775'
down_revision = 'c804329ffeda'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('topics',
                  sa.Column('next_topic', sa.String(36),
                            sa.ForeignKey('topics.id', ondelete='SET NULL'),
                            nullable=True, default=None))
    op.add_column('jobs',
                  sa.Column('previous_job_id', sa.String(36),
                            sa.ForeignKey('jobs.id', ondelete='SET NULL'),
                            nullable=True, default=None))
    op.add_column('jobs',
                  sa.Column('is_upgrade', sa.Boolean, default=False))

    op.add_column('remotecis',
                  sa.Column('allow_upgrade_job', sa.BOOLEAN, default=False))


def downgrade():
    pass
