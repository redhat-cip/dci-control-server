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

"""add_roles

Revision ID: 64c7711477db
Revises: b94c70c226a9
Create Date: 2017-05-30 09:37:34.976639

"""

# revision identifiers, used by Alembic.
revision = '64c7711477db'
down_revision = 'b94c70c226a9'
branch_labels = None
depends_on = None

import datetime
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy import sql
import dci.common.utils as utils

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
    sa.Column('team_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('teams.id', ondelete='CASCADE'),
              nullable=False),
    sa.UniqueConstraint('label', 'team_id', name='roles_label_team_id_key'),
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

USER_ROLES = ['user', 'admin']
ROLES_ENUM = sa.Enum(*USER_ROLES, name='roles_enum')

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
    sa.Column('role_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('roles.id', ondelete='SET NULL')),
    sa.Column('team_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('teams.id', ondelete='CASCADE'),
              nullable=False),
    sa.Index('users_team_id_idx', 'team_id'),
    sa.Column('state', STATES, default='active')
)


def upgrade():
    op.add_column('users', sa.Column('role_id', pg.UUID(as_uuid=True),
                                     sa.ForeignKey('roles.id',
                                                   ondelete='SET NULL')))

    db_conn = op.get_bind()

    team_admin_id = str(
        db_conn.execute(
            TEAMS.select().where(TEAMS.c.name == 'admin')
        ).fetchone()['id']
    )

    super_admin_role_id = utils.gen_uuid()
    super_admin_role = {
        'id': super_admin_role_id,
        'created_at': datetime.datetime.utcnow().isoformat(),
        'updated_at': datetime.datetime.utcnow().isoformat(),
        'etag': utils.gen_etag(),
        'name': 'Super Admin',
        'label': 'SUPER_ADMIN',
        'description': 'Admin of the platform',
    }

    admin_role_id = utils.gen_uuid()
    admin_role = {
        'id': admin_role_id,
        'created_at': datetime.datetime.utcnow().isoformat(),
        'updated_at': datetime.datetime.utcnow().isoformat(),
        'etag': utils.gen_etag(),
        'name': 'Admin',
        'label': 'ADMIN',
        'description': 'Admin of a team',
    }

    user_role_id = utils.gen_uuid()
    user_role = {
        'id': user_role_id,
        'created_at': datetime.datetime.utcnow().isoformat(),
        'updated_at': datetime.datetime.utcnow().isoformat(),
        'etag': utils.gen_etag(),
        'name': 'User',
        'label': 'USER',
        'description': 'Regular User',
    }

    db_conn.execute(ROLES.insert().values(**super_admin_role))
    db_conn.execute(ROLES.insert().values(**admin_role))
    db_conn.execute(ROLES.insert().values(**user_role))

    db_conn.execute(
        USERS.update().
        where(sql.and_(USERS.c.role == 'admin',
                       USERS.c.team_id == team_admin_id)).
        values(role_id=super_admin_role_id)
    )
    db_conn.execute(
        USERS.update().
        where(sql.and_(USERS.c.role == 'admin',
                       USERS.c.team_id != team_admin_id)).
        values(role_id=admin_role_id)
    )
    db_conn.execute(
        USERS.update().where(USERS.c.role == 'user').
        values(role_id=user_role_id)
    )


def downgrade():
    pass
