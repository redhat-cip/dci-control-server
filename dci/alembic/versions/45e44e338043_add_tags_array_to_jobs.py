#
# Copyright (C) 2020 Red Hat, Inc
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

"""Add tags array to jobs

Revision ID: 45e44e338043
Revises: 49363052bd7d
Create Date: 2020-03-19 16:01:17.853976

"""

# revision identifiers, used by Alembic.
revision = '45e44e338043'
down_revision = '49363052bd7d'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


def upgrade():
    op.add_column('jobs', sa.Column('tag', pg.ARRAY(sa.Text), default=[]))


def downgrade():
    pass
