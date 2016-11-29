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

"""Adds jobs etag and created_at columns

Revision ID: c804329ffeda
Revises: 4f5d47b61a9d
Create Date: 2016-11-28 01:53:26.318044

"""

# revision identifiers, used by Alembic.
revision = 'c804329ffeda'
down_revision = '4f5d47b61a9d'
branch_labels = None
depends_on = None

import datetime

from alembic import op
import sqlalchemy as sa

import dci.common.utils as utils


def upgrade():
    op.add_column('metas',
                  sa.Column('updated_at', sa.DateTime(),
                            onupdate=datetime.datetime.utcnow,
                            default=datetime.datetime.utcnow, nullable=False))
    op.add_column('metas',
                  sa.Column('etag', sa.String(40), nullable=False,
                            default=utils.gen_etag,
                            onupdate=utils.gen_etag))


def downgrade():
    pass
