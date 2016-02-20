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

"""Add comment on jobs

Revision ID: 56738540a625
Revises: e4d599796fd4
Create Date: 2016-03-02 14:03:30.638412

"""

# revision identifiers, used by Alembic.
revision = '56738540a625'
down_revision = 'e4d599796fd4'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('jobs', sa.Column('comment', sa.Text))


def downgrade():
    pass
