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

"""Add remoteci configurations

Revision ID: 5874e497e4d8
Revises: 64c7711477db
Create Date: 2017-06-08 19:46:55.427115

"""

# revision identifiers, used by Alembic.
revision = '5874e497e4d8'
down_revision = 'cba07e5d607d'
branch_labels = None
depends_on = None

import datetime

from alembic import op
from sqlalchemy.dialects import postgresql as pg
import sqlalchemy as sa

import sqlalchemy_utils as sa_utils

from dci.common import utils


def upgrade():
    states = pg.ENUM('active', 'inactive', 'archived',
                     name='states', create_type=False)
    op.create_table(
        'rconfigurations',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
                  default=utils.gen_uuid),
        sa.Column('created_at', sa.DateTime(),
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('updated_at', sa.DateTime(),
                  onupdate=datetime.datetime.utcnow,
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('etag', sa.String(40), nullable=False,
                  default=utils.gen_etag, onupdate=utils.gen_etag),
        sa.Column('state', states, default='active'),
        sa.Column('topic_id', pg.UUID(as_uuid=True),
                  sa.ForeignKey('topics.id', ondelete='CASCADE'),
                  nullable=True),
        sa.Column('component_types', pg.JSON, default=[]),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('data', sa_utils.JSONType)
    )

    op.create_table(
        'remotecis_rconfigurations',
        sa.Column('remoteci_id', pg.UUID(as_uuid=True),
                  sa.ForeignKey('remotecis.id', ondelete='CASCADE'),
                  nullable=False, primary_key=True),
        sa.Column('rconfiguration_id', pg.UUID(as_uuid=True),
                  sa.ForeignKey('rconfigurations.id', ondelete='CASCADE'),
                  nullable=False, primary_key=True)
    )


def downgrade():
    pass
