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

"""Adds files_changes table

Revision ID: 61b68c2d66b5
Revises: 01feb29bf129
Create Date: 2017-04-20 15:59:42.636310

"""

# revision identifiers, used by Alembic.
revision = '61b68c2d66b5'
down_revision = '01feb29bf129'
branch_labels = None
depends_on = None

import datetime

from alembic import op
import sqlalchemy as sa

from dci.db import models

from sqlalchemy.dialects import postgresql as pg


def upgrade():
    op.create_table(
        'files_events',
        sa.Column('id', sa.Integer, primary_key=True,
                  autoincrement=True),
        sa.Column('created_at', sa.DateTime(),
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('file_id', pg.UUID(as_uuid=True),
                  sa.ForeignKey('files.id'),
                  nullable=False),
        sa.Column('action', models.FILES_ACTIONS,
                  default=models.FILES_CREATE)
    )


def downgrade():
    pass
