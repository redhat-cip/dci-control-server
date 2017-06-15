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

"""add rconfiguration_id in jobs

Revision ID: 491df8d6fb62
Revises: 014984a4512f
Create Date: 2017-06-15 17:56:24.946112

"""

# revision identifiers, used by Alembic.
revision = '491df8d6fb62'
down_revision = '014984a4512f'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


def upgrade():
    op.add_column('jobs', sa.Column('rconfiguration_id', pg.UUID(as_uuid=True),
                                    sa.ForeignKey('rconfigurations.id'),
                                    nullable=True))
    op.create_index('jobs_rconfiguration_id_idx',
                    'jobs',
                    ['rconfiguration_id'])


def downgrade():
    pass
