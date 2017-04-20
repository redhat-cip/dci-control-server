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

"""create_roles_table

Revision ID: 4a7aebcd0c28
Revises: 01feb29bf129
Create Date: 2017-04-21 12:57:18.008293

"""

# revision identifiers, used by Alembic.
revision = '4a7aebcd0c28'
down_revision = '01feb29bf129'
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

    op.execute('ALTER TYPE roles RENAME TO roles_enum')

    op.create_table(
        'roles',
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
        sa.Column('label', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('team_id', pg.UUID(as_uuid=True),
                  sa.ForeignKey('teams.id', ondelete='CASCADE'),
                  nullable=False),
        sa.UniqueConstraint('label', 'team_id',
                            name='roles_label_team_id_key'),
        sa.Column('state', states, default='active'),
    )


def downgrade():
    pass
