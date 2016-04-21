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

"""Add component_types to jobdefinitions

Revision ID: 18327b41e11d
Revises: 89638be0fc0f
Create Date: 2016-04-21 19:41:43.582457

"""

# revision identifiers, used by Alembic.
revision = '18327b41e11d'
down_revision = '89638be0fc0f'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgres as pg


def upgrade():
    op.add_column('jobdefinitions', sa.Column('component_types',
                                              pg.JSON, default=[]))


def downgrade():
    pass
