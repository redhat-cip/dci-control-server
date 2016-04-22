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

"""Add join table join_jobs_components

Revision ID: e6c96dce3b95
Revises: 18327b41e11d
Create Date: 2016-04-22 11:12:31.786483

"""

# revision identifiers, used by Alembic.
revision = 'e6c96dce3b95'
down_revision = '18327b41e11d'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'jobs_components',
        sa.Column('job_id', sa.String(36),
                  sa.ForeignKey('jobs.id', ondelete="CASCADE"),
                  nullable=False, primary_key=True),
        sa.Column('component_id', sa.String(36),
                  sa.ForeignKey('components.id', ondelete="CASCADE"),
                  nullable=False, primary_key=True)
    )


def downgrade():
    pass
