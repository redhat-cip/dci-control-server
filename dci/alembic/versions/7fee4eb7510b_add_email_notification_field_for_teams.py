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

"""Add email notification field for teams

Revision ID: 7fee4eb7510b
Revises: 8a64d57a77d3
Create Date: 2016-10-31 09:27:39.502507

"""

# revision identifiers, used by Alembic.
revision = '7fee4eb7510b'
down_revision = '8a64d57a77d3'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('teams',
                  sa.Column('email', sa.String(255), nullable=True))
    op.add_column('teams',
                  sa.Column('notification', sa.BOOLEAN, default=False))


def downgrade():
    pass
