#
# Copyright (C) 2017 Red Hat, Inc
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

"""create jobresults table

Revision ID: 429a312c5e85
Revises: 1bb42ff54435
Create Date: 2017-03-30 07:36:44.830095

"""

# revision identifiers, used by Alembic.
revision = '429a312c5e85'
down_revision = '1bb42ff54435'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

import dci.common.utils as utils


def upgrade():
    op.create_table(
        'tests_results',
        sa.Column('id', postgresql.UUID(as_uuid=True),
                  primary_key=True, default=utils.gen_uuid),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('total', sa.Integer(), nullable=True),
        sa.Column('success', sa.Integer(), nullable=True),
        sa.Column('skips', sa.Integer(), nullable=True),
        sa.Column('failures', sa.Integer(), nullable=True),
        sa.Column('errors', sa.Integer(), nullable=True),
        sa.Column('time', sa.Integer(), nullable=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('jobs.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('file_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('files.id', ondelete='CASCADE'),
                  nullable=False),
    )


def downgrade():
    op.drop_table('tests_results')
