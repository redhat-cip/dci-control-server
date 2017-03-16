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

Revision ID: ca50e442150f
Revises: 1bb42ff54435
Create Date: 2017-03-16 10:52:38.468706

"""

# revision identifiers, used by Alembic.
revision = 'ca50e442150f'
down_revision = '1bb42ff54435'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.create_table(
        'jobresults',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('total', sa.Integer(), nullable=True),
        sa.Column('success', sa.Integer(), nullable=True),
        sa.Column('skips', sa.Integer(), nullable=True),
        sa.Column('failures', sa.Integer(), nullable=True),
        sa.Column('errors', sa.Integer(), nullable=True),
        sa.Column('time', sa.Integer(), nullable=True),
        sa.Column('jobstate_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['jobstate_id'], ['jobstates.id'],
                                ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('jobresults')
