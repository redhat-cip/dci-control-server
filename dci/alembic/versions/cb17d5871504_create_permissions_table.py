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

"""create_permissions_table

Revision ID: cb17d5871504
Revises: 5874e497e4d8
Create Date: 2017-06-23 13:19:38.873448

"""

# revision identifiers, used by Alembic.
revision = 'cb17d5871504'
down_revision = '5874e497e4d8'
branch_labels = None
depends_on = None

from alembic import op
import datetime
import sqlalchemy as sa
import dci.common.utils as utils
from sqlalchemy.dialects import postgresql as pg


def upgrade():
    states = pg.ENUM('active', 'inactive', 'archived',
                     name='states', create_type=False)

    op.create_table(
        'permissions',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
                  default=utils.gen_uuid),
        sa.Column('created_at', sa.DateTime(),
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('updated_at', sa.DateTime(),
                  onupdate=datetime.datetime.utcnow,
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('etag', sa.String(40), nullable=False,
                  default=utils.gen_etag,
                  onupdate=utils.gen_etag),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('label', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text),
        sa.Column('state', states, default='active'),
    )

    op.create_table(
        'roles_permissions',
        sa.Column('role_id', pg.UUID(as_uuid=True),
                  sa.ForeignKey('roles.id', ondelete='CASCADE'),
                  nullable=False, primary_key=True),
        sa.Column('permission_id', pg.UUID(as_uuid=True),
                  sa.ForeignKey('permissions.id', ondelete='CASCADE'),
                  nullable=False, primary_key=True)
    )


def downgrade():
    pass
