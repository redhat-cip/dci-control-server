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

Revision ID: c0fc54f5be15
Revises: 418030c694de
Create Date: 2016-07-12 11:40:23.968854

"""

# revision identifiers, used by Alembic.
revision = 'c0fc54f5be15'
down_revision = '418030c694de'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('jobs',
                  sa.Column('user_agent', sa.String(255), default=None))


def downgrade():
    pass
