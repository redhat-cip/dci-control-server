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

"""Add user_agent field to job table

Revision ID: 01babf3af0b4
Revises: db239f63b5df
Create Date: 2016-07-13 13:41:23.870915

"""

# revision identifiers, used by Alembic.
revision = '01babf3af0b4'
down_revision = 'db239f63b5df'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('jobs',
                  sa.Column('user_agent', sa.String(255), default=None))
    op.add_column('jobs',
                  sa.Column('dciclient_version', sa.String(255),
                            default=None))


def downgrade():
    pass
