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

"""add_remoteci_role_id_field

Revision ID: e240bb5e7141
Revises: 6d70b87c46b0
Create Date: 2017-10-09 13:48:37.937124

"""

# revision identifiers, used by Alembic.
revision = 'e240bb5e7141'
down_revision = '6d70b87c46b0'
branch_labels = None
depends_on = None

import datetime
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy import sql
import dci.common.utils as utils
from dci.common import signature
import sqlalchemy_utils as sa_utils


RESOURCE_STATES = ['active', 'inactive', 'archived']
STATES = sa.Enum(*RESOURCE_STATES, name='states')

ROLES = sa.Table(
    'roles', sa.MetaData(),
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
    sa.Column('name', sa.String(255), nullable=False),
    sa.Column('label', sa.String(255), nullable=False),
    sa.Column('description', sa.Text),
    sa.UniqueConstraint('label', name='roles_label_key'),
    sa.Column('state', STATES, default='active')
)

REMOTECIS = sa.Table(
    'remotecis', sa.MetaData(),
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
    sa.Column('name', sa.String(255)),
    sa.Column('data', sa_utils.JSONType),
    sa.Column('api_secret', sa.String(64), default=signature.gen_secret),
    sa.Column('team_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('teams.id', ondelete='CASCADE'),
              nullable=False),
    sa.Column('role_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('roles.id', ondelete='SET NULL')),
    sa.Index('remotecis_team_id_idx', 'team_id'),
    sa.UniqueConstraint('name', 'team_id', name='remotecis_name_team_id_key'),
    sa.Column('allow_upgrade_job', sa.BOOLEAN, default=False),
    sa.Column('public', sa.BOOLEAN, default=False),
    sa.Column('state', STATES, default='active'),
)


def upgrade():
    op.add_column('remotecis', sa.Column('role_id', pg.UUID(as_uuid=True),
                                         sa.ForeignKey('roles.id',
                                                       ondelete='SET NULL')))
    db_conn = op.get_bind()

    remoteci_role_id = str(
        db_conn.execute(
            ROLES.select().where(ROLES.c.label == 'REMOTECI')
        ).fetchone()['id']
    )

    db_conn.execute(REMOTECIS.update().values(role_id=remoteci_role_id))


def downgrade():
    pass
