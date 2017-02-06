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

"""create_components_issues_table

Revision ID: 0327fd239d3f
Revises: 1bb42ff54435
Create Date: 2017-04-10 16:06:50.325405

"""

# revision identifiers, used by Alembic.
revision = '0327fd239d3f'
down_revision = '1bb42ff54435'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


def upgrade():
    op.create_table(
        'components_issues',
        sa.Column('component_id', pg.UUID(as_uuid=True),
                  sa.ForeignKey('components.id', ondelete="CASCADE"),
                  nullable=False, primary_key=True),
        sa.Column('issue_id', pg.UUID(as_uuid=True),
                  sa.ForeignKey('issues.id', ondelete="CASCADE"),
                  nullable=False, primary_key=True),
        sa.Column('user_id', pg.UUID(as_uuid=True),
                  sa.ForeignKey('users.id'),
                  nullable=False),
        sa.Index('components_issues_user_id_idx', 'user_id')
    )

    op.add_column(
        'jobs_issues',
        sa.Column('user_id', pg.UUID(as_uuid=True),
                  sa.ForeignKey('users.id'))
    )
    op.create_index('jobs_issues_user_id_idx', 'jobs_issues', ['user_id'])


def downgrade():
    pass
