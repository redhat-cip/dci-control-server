#
# Copyright (C) 2016 Red Hat, Inc
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

"""Alter test to belong to team

Revision ID: 9c639866e1b4
Revises: f1940287976b
Create Date: 2016-08-05 18:06:29.733214

"""

# revision identifiers, used by Alembic.
revision = '9c639866e1b4'
down_revision = '455efd62c24b'
branch_labels = None
depends_on = None

from alembic import op
import datetime
import sqlalchemy as sa
import sqlalchemy_utils as sa_utils
from sqlalchemy import sql

from dci.common import utils

_TEAMS = sa.Table(
    'teams', sa.MetaData(),
    sa.Column('id', sa.String(36), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
    sa.Column('name', sa.String(255), unique=True, nullable=False))

_TESTS = sa.Table(
    'tests', sa.MetaData(),
    sa.Column('id', sa.String(36), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('name', sa.String(255), nullable=False, unique=True),
    sa.Column('data', sa_utils.JSONType),
    sa.Column('team_id', sa.String(36),
              sa.ForeignKey('teams.id', ondelete='CASCADE'),
              nullable=True))


def upgrade():

    db_conn = op.get_bind()
    admin_team = (
        db_conn.execute(sql.select([_TEAMS])
                        .where(_TEAMS.c.name == 'admin'))
        .first()
    )
    op.add_column('tests', sa.Column('team_id', sa.String(36),
                  sa.ForeignKey('teams.id', ondelete="CASCADE"),
                  nullable=True))
    op.drop_column('tests', 'topic_id')
    op.create_table(
        'topic_tests',
        sa.Column('topic_id', sa.String(36),
                  sa.ForeignKey('topics.id', ondelete='CASCADE'),
                  nullable=False, primary_key=True),
        sa.Column('test_id', sa.String(36),
                  sa.ForeignKey('tests.id', ondelete='CASCADE'),
                  nullable=False, primary_key=True)
    )
    if admin_team_id:
        op.execute(_TESTS.update().values(team_id=admin_team['id']))

    op.alter_column('tests', 'team_id', nullable=False)


def downgrade():
    pass
