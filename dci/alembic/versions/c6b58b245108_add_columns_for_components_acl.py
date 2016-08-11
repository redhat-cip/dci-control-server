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

"""add columns for components ACL

Revision ID: c6b58b245108
Revises: f1940287976b
Create Date: 2016-08-10 09:51:23.496026

"""

# revision identifiers, used by Alembic.
revision = 'c6b58b245108'
down_revision = '9c639866e1b4'
branch_labels = None
depends_on = None

import datetime

from alembic import op
import sqlalchemy as sa

from dci.common import utils


def upgrade():
    op.add_column('teams',
                  sa.Column('country', sa.String(255), default='Foreign',
                  nullable=False, server_default='Foreign'))
    op.add_column('components',
                  sa.Column('updated_at', sa.DateTime(),
                            default=datetime.datetime.utcnow, nullable=False))
    op.add_column('components',
                  sa.Column('export_control', sa.BOOLEAN,
                            nullable=False, default=False))
    op.add_column('components',
                  sa.Column('etag', sa.String(40), nullable=False,
                            default=utils.gen_etag, onupdate=utils.gen_etag))
    op.create_table(
        'component_files',
        sa.Column('id', sa.String(36), primary_key=True,
                  default=utils.gen_uuid),
        sa.Column('created_at', sa.DateTime(),
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('mime', sa.String),
        sa.Column('md5', sa.String(32)),
        sa.Column('size', sa.BIGINT, nullable=True),
        sa.Column('component_id', sa.String(36),
                  sa.ForeignKey('components.id', ondelete='CASCADE'),
                  nullable=True))


def downgrade():
    pass
