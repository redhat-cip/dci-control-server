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

"""create_admin_user_and_team

Revision ID: bdce8119299f
Revises: 820d50460b68
Create Date: 2017-05-23 10:36:32.190390

"""

# revision identifiers, used by Alembic.
revision = 'bdce8119299f'
down_revision = '820d50460b68'
branch_labels = None
depends_on = None

from alembic import op
import datetime
import sqlalchemy as sa
import dci.common.utils as utils
import dci.auth as auth
from sqlalchemy.dialects import postgresql as pg

USER_ROLES = ['user', 'admin']
ROLES_ENUM = sa.Enum(*USER_ROLES, name='roles_enum')

RESOURCE_STATES = ['active', 'inactive', 'archived']
STATES = sa.Enum(*RESOURCE_STATES, name='states')

USERS = sa.Table(
    'users', sa.MetaData(),
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
    sa.Column('name', sa.String(255), nullable=False, unique=True),
    sa.Column('password', sa.Text, nullable=False),
    sa.Column('role', ROLES_ENUM, default=USER_ROLES[0], nullable=False),
    sa.Column('team_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('teams.id', ondelete='CASCADE'),
              nullable=False),
    sa.Index('users_team_id_idx', 'team_id'),
    sa.Column('state', STATES, default='active')
)

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

    t_admin = db_conn.execute(TEAMS.select(TEAMS.c.name == 'admin')).fetchall()

    if not len(t_admin):
        team_id = utils.gen_uuid()
        team_values = {
            'id': team_id,
            'created_at': datetime.datetime.utcnow().isoformat(),
            'updated_at': datetime.datetime.utcnow().isoformat(),
            'etag': utils.gen_etag(),
            'name': 'admin'
        }
        db_conn.execute(TEAMS.insert().values(**team_values))

        user_id = utils.gen_uuid()
        user_values = {
            'id': user_id,
            'created_at': datetime.datetime.utcnow().isoformat(),
            'updated_at': datetime.datetime.utcnow().isoformat(),
            'etag': utils.gen_etag(),
            'name': 'admin',
            'role': 'admin',
            'team_id': team_id,
            'password': auth.hash_password('password'),
        }
        db_conn.execute(USERS.insert().values(**user_values))


def downgrade():
    pass
