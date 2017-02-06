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

Revision ID: 43363af27126
Revises: 75a91edc23b8
Create Date: 2017-02-06 12:41:42.290460

"""

# revision identifiers, used by Alembic.
revision = '43363af27126'
down_revision = '75a91edc23b8'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():

    op.create_table(
        'components_issues',
        sa.Column('component_id', sa.String(36),
                  sa.ForeignKey('components.id', ondelete="CASCADE"),
                  nullable=False, primary_key=True),
        sa.Column('issue_id', sa.String(36),
                  sa.ForeignKey('issues.id', ondelete="CASCADE"),
                  nullable=False, primary_key=True),
        sa.Column('user_id', sa.String(36),
                  sa.ForeignKey('users.id'),
                  nullable=False, primary_key=True)
    )


def downgrade():
    pass
