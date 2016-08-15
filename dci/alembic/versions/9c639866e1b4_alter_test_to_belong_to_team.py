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

"""Alter test to belong to team

Revision ID: 9c639866e1b4
Revises: f1940287976b
Create Date: 2016-08-05 18:06:29.733214

"""

# revision identifiers, used by Alembic.
revision = '9c639866e1b4'
down_revision = 'f1940287976b'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('tests', sa.Column('team_id', sa.String(36),
                  sa.ForeignKey('teams.id', ondelete="CASCADE"),
                  nullable=False, primary_key=True))
    op.drop_column('tests', 'topic_id')
    op.create_table(
        'topic_tests',
        sa.Column('topic_id', sa.String(36),
                  sa.ForeignKey('topics.id', ondelete='CASCADE'),
                  nullable=False, primary_key=True),
        sa.Column('test_id', sa.String(36),
                  sa.ForeignKey('tests.id', ondelete='CASCADE'),
                  nullable=False, primary_key=True)
    )


def downgrade():
    pass
