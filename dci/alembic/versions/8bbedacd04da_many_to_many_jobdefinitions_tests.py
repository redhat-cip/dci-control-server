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

"""many to many jobdefinitions tests

Revision ID: 8bbedacd04da
Revises: 463d8023ce19
Create Date: 2016-04-13 10:41:58.700687

"""

# revision identifiers, used by Alembic.
revision = '8bbedacd04da'
down_revision = '463d8023ce19'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    constraint = 'jobdefinitions_test_id_fkey'
    op.drop_column('jobdefinitions', 'test_id')
    op.drop_constraint(constraint, 'jobdefinitions')

    op.create_table(
        'jobdefinition_tests',
        sa.Column('jobdefinition_id', sa.String(36),
                  sa.ForeignKey('jobdefinitions.id', ondelete="CASCADE"),
                  nullable=False),
        sa.Column('test_id', sa.String(36),
                  sa.ForeignKey('tests.id', ondelete="CASCADE"),
                  nullable=False),
        sa.UniqueConstraint('jobdefinition_id', 'test_id')
    )


def downgrade():
    """Not supported at this time, will be implemented later"""
    pass
