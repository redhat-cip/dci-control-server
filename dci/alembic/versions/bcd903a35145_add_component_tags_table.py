#
# Copyright (C) 2018 Red Hat, Inc
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

"""Add component tags table

Revision ID: bcd903a35145
Revises: 772428482e52
Create Date: 2018-07-09 11:47:28.174830

"""

# revision identifiers, used by Alembic.
revision = 'bcd903a35145'
down_revision = '772428482e52'
branch_labels = None
depends_on = None

from dci.common import utils

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


def upgrade():
    op.create_table(
        'join_components_tags',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
                  default=utils.gen_uuid),
        sa.Column('value', sa.String(255), nullable=False, primary_key=True)
    )


def downgrade():
    pass
