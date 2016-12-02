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

"""create_state_column

Revision ID: 75a91edc23b8
Revises: 82f4f4d14775
Create Date: 2017-01-30 09:55:25.386279

"""

# revision identifiers, used by Alembic.
revision = '75a91edc23b8'
down_revision = '82f4f4d14775'
branch_labels = None
depends_on = None

import datetime

from alembic import op
import sqlalchemy as sa

import dci.common.utils as utils


def upgrade():
    states = sa.Enum('active', 'inactive', 'archived', name='states')

    op.add_column('components',
                  sa.Column('state', states, nullable=False))

    op.add_column('topics',
                  sa.Column('state', states, nullable=False))

    op.add_column('tests',
                  sa.Column('updated_at', sa.DateTime(),
                            onupdate=datetime.datetime.utcnow,
                            default=datetime.datetime.utcnow, nullable=False))
    op.add_column('tests',
                  sa.Column('etag', sa.String(40), nullable=False,
                            default=utils.gen_etag,
                            onupdate=utils.gen_etag))
    op.add_column('tests',
                  sa.Column('state', states, nullable=False))

    op.add_column('teams',
                  sa.Column('state', states, nullable=False))

    op.add_column('jobdefinitions',
                  sa.Column('state', states, nullable=False))

    op.add_column('remotecis',
                  sa.Column('state', states, nullable=False))

    op.add_column('jobs',
                  sa.Column('state', states, nullable=False))

    op.add_column('files',
                  sa.Column('updated_at', sa.DateTime(),
                            onupdate=datetime.datetime.utcnow,
                            default=datetime.datetime.utcnow, nullable=False))
    op.add_column('files',
                  sa.Column('etag', sa.String(40), nullable=False,
                            default=utils.gen_etag,
                            onupdate=utils.gen_etag))
    op.add_column('files',
                  sa.Column('state', states, nullable=False))

    op.add_column('component_files',
                  sa.Column('state', states, nullable=False))


def downgrade():
    pass

