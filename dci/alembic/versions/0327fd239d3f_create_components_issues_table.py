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

"""create_components_issues_table

Revision ID: 0327fd239d3f
Revises: 1bb42ff54435
Create Date: 2017-04-10 16:06:50.325405

"""

# revision identifiers, used by Alembic.
revision = '0327fd239d3f'
down_revision = '1bb42ff54435'
branch_labels = None
depends_on = None

import datetime
from alembic import op
from dci.common import utils
from dci.db import models
import sqlalchemy as sa
from sqlalchemy import sql
from sqlalchemy import text
from sqlalchemy.dialects import postgresql as pg

metadata = sa.MetaData()

USER_ROLES = ['user', 'admin']
ROLES = sa.Enum(*USER_ROLES, name='roles')

RESOURCE_STATES = ['active', 'inactive', 'archived']
STATES = sa.Enum(*RESOURCE_STATES, name='states')

_USERS = sa.Table(
    'users', metadata,
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
    sa.Column('role', ROLES, default=USER_ROLES[0], nullable=False),
    sa.Column('team_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('teams.id', ondelete='CASCADE'),
              nullable=False),
    sa.Index('users_team_id_idx', 'team_id'),
    sa.Column('state', STATES, default='active')
)


def upgrade():
    db_conn = op.get_bind()
    admin_id = (
        db_conn.execute(sql.select([_USERS])
                        .where(_USERS.c.name == 'admin')).first()
    )
    op.create_table(
        'components_issues',
        sa.Column('component_id', pg.UUID(as_uuid=True),
                  sa.ForeignKey('components.id', ondelete="CASCADE"),
                  nullable=False, primary_key=True),
        sa.Column('issue_id', pg.UUID(as_uuid=True),
                  sa.ForeignKey('issues.id', ondelete="CASCADE"),
                  nullable=False, primary_key=True),
        sa.Column('user_id', pg.UUID(as_uuid=True),
                  sa.ForeignKey('users.id'),
                  nullable=False),
        sa.Index('components_issues_user_id_idx', 'user_id')
    )

    op.add_column(
        'jobs_issues',
        sa.Column('user_id', pg.UUID(as_uuid=True),
                  sa.ForeignKey('users.id'), nullable=False,
                  server_default=text(admin_id['id']))
    )
    op.create_index('jobs_issues_user_id_idx', 'jobs_issues', ['user_id'])


def downgrade():
    pass
