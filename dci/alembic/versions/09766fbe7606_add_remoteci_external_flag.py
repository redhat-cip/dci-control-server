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

"""Add remoteci external flag

Revision ID: 09766fbe7606
Revises: e240bb5e7141
Create Date: 2017-10-19 14:08:01.663046

"""

# revision identifiers, used by Alembic.
revision = '09766fbe7606'
down_revision = 'e240bb5e7141'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('remotecis', sa.Column('external', sa.BOOLEAN, default=True))


def downgrade():
    pass
