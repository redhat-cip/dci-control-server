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

"""add_team_id_to_product

Revision ID: 49b66daed760
Revises: f381f939cd0b
Create Date: 2017-08-08 13:10:01.916380

"""

# revision identifiers, used by Alembic.
revision = '49b66daed760'
down_revision = 'f381f939cd0b'
branch_labels = None
depends_on = None

import datetime
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
import dci.common.utils as utils

RESOURCE_STATES = ['active', 'inactive', 'archived']
STATES = sa.Enum(*RESOURCE_STATES, name='states')

TEAMS = sa.Table(
    'teams', sa.MetaData(),
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
    sa.Column('name', sa.String(255), unique=True, nullable=False),
    sa.Column('country', sa.String(255), nullable=True),
    sa.Column('email', sa.String(255), nullable=True),
    sa.Column('notification', sa.BOOLEAN, default=False),
    sa.Column('state', STATES, default='active')
)


def upgrade():

    db_conn = op.get_bind()

    team_admin_id = str(
        db_conn.execute(
            TEAMS.select().where(TEAMS.c.name == 'admin')
        ).fetchone()['id']
    )

    op.add_column('products', sa.Column('team_id', pg.UUID(as_uuid=True),
                                        sa.ForeignKey('teams.id',
                                                      ondelete='SET NULL'),
                                        nullable=False,
                                        server_default=team_admin_id))


def downgrade():
    pass
