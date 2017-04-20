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

Revision ID: f2009a32d88c
Revises: ad1134e557de
Create Date: 2017-05-11 12:29:12.324445

"""

# revision identifiers, used by Alembic.
revision = 'f2009a32d88c'
down_revision = 'ad1134e557de'
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
