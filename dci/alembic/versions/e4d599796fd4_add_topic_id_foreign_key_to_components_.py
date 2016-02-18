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


def upgrade():
    op.add_column('components',
                  sa.Column('topic_id', sa.String(36),
                            sa.ForeignKey('topics.id', ondelete="CASCADE"),
                            nullable=False))
    op.add_column('tests',
                  sa.Column('topic_id', sa.String(36),
                            sa.ForeignKey('topics.id', ondelete="CASCADE"),
                            nullable=False))
    op.add_column('jobdefinitions',
                  sa.Column('topic_id', sa.String(36),
                            sa.ForeignKey('topics.id', ondelete="CASCADE"),
                            nullable=False))


def downgrade():
    """Not supported at this time, will be implemented later"""
