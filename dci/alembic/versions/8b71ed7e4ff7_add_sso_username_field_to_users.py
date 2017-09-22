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

"""Add sso_username field to users

Revision ID: 8b71ed7e4ff7
Revises: 6f875bc66ca9
Create Date: 2017-09-26 17:39:18.206294

"""

# revision identifiers, used by Alembic.
revision = '8b71ed7e4ff7'
down_revision = '6f875bc66ca9'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('users', sa.Column('sso_username', sa.String(255),
                                     nullable=True, unique=True))


def downgrade():
    pass
