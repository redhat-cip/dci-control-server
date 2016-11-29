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

"""add authentication secrets

Revision ID: fef5ee50d196
Revises: ad1134e557de
Create Date: 2016-11-22 22:49:58.394669

"""

# revision identifiers, used by Alembic.
revision = 'fef5ee50d196'
down_revision = 'ad1134e557de'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('remotecis', sa.Column('api_secret', sa.String(64)))


def downgrade():
    op.drop_column('remotecis', sa.Column('api_secret'))
