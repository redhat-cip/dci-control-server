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

"""Add external flag to team

Revision ID: 827c558895bc
Revises: 6bdcadae9419
Create Date: 2017-10-23 16:46:02.760808

"""

# revision identifiers, used by Alembic.
revision = '827c558895bc'
down_revision = '6bdcadae9419'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('teams', sa.Column('external', sa.BOOLEAN, default=True))


def downgrade():
    pass
