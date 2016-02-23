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

"""Add job_files table

Revision ID: f020057b1680
Revises: c92c843fc800
Create Date: 2016-02-23 11:13:17.111105

"""

# revision identifiers, used by Alembic.
revision = 'f020057b1680'
down_revision = 'c92c843fc800'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'job_files',
        sa.Column('job_id', sa.String(36),
                  sa.ForeignKey('jobs.id', ondelete="CASCADE"),
                  nullable=False, primary_key=True),
        sa.Column('file_id', sa.String(36),
                  sa.ForeignKey('files.id', ondelete="CASCADE"),
                  nullable=False, primary_key=True)
    )

    op.alter_column(
        table_name='files',
        column_name='jobstate_id',
        nullable=True
    )


def downgrade():
    """Not supported at this time, will be implemented later"""
    pass
