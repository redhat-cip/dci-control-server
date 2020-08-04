#
# Copyright (C) 2020 Red Hat, Inc
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

"""Add team id to components

Revision ID: c5bbe7b63a
Revises: 1d9624cbf1e
Create Date: 2020-08-03 18:14:16.796411

"""

# revision identifiers, used by Alembic.
revision = 'c5bbe7b63a'
down_revision = '1d9624cbf1e'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


def upgrade():
    op.add_column('components',
                  sa.Column('team_id', pg.UUID(as_uuid=True),
                            sa.ForeignKey('teams.id', ondelete='CASCADE'),
                            nullable=True))


def downgrade():
    pass
