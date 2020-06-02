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

"""add virtuals to topics

Revision ID: 1025384d35b
Revises: 236e3b2c2a3d
Create Date: 2020-05-26 13:59:45.794650

"""

# revision identifiers, used by Alembic.
revision = '1025384d35b'
down_revision = '503ae4ae05'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


def upgrade():
    op.add_column(
        'topics',
        sa.Column('virtual', sa.BOOLEAN, default=False, server_default='false'))
    op.add_column(
        'topics',
        sa.Column('real_topic_id', pg.UUID(as_uuid=True),
                  sa.ForeignKey('topics.id'),
                  nullable=True))


def downgrade():
    pass
