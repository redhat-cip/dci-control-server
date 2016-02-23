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

"""add job files table

Revision ID: a199a93a0bc6
Revises: 099abdadf83a
Create Date: 2016-02-25 15:26:49.705542

"""

# revision identifiers, used by Alembic.
revision = 'a199a93a0bc6'
down_revision = '099abdadf83a'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():

    op.add_column(
        'files',
        sa.Column('job_id', sa.String(36),
                  sa.ForeignKey('jobs.id', ondelete="CASCADE"),
                  nullable=True, primary_key=True)
    )

    op.alter_column(
        table_name='files',
        column_name='jobstate_id',
        nullable=True
    )


def downgrade():
    """Not supported at this time, will be implemented later"""
    pass
