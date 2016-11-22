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

"""Adds jobs metas information

Revision ID: 4f5d47b61a9d
Revises: 8a64d57a77d3
Create Date: 2016-11-21 13:29:13.078013

"""

# revision identifiers, used by Alembic.
revision = '4f5d47b61a9d'
down_revision = '7fee4eb7510b'
branch_labels = None
depends_on = None

import datetime

from alembic import op
import sqlalchemy as sa

import dci.common.utils as utils


def upgrade():
    op.create_table(
        'metas',
        sa.Column('id', sa.String(36), primary_key=True,
                  default=utils.gen_uuid),
        sa.Column('created_at', sa.DateTime(),
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('updated_at', sa.DateTime(),
                  onupdate=datetime.datetime.utcnow,
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('etag', sa.String(40), nullable=False,
                  default=utils.gen_etag,
                  onupdate=utils.gen_etag),
        sa.Column('name', sa.Text),
        sa.Column('value', sa.Text),
        sa.Column('job_id', sa.String(36),
                  sa.ForeignKey('jobs.id', ondelete='CASCADE'),
                  nullable=False)
    )


def downgrade():
    pass
