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

"""Add column to file to link result to tests

Revision ID: 6bbbf58ed9de
Revises: c804329ffeda
Create Date: 2017-01-19 13:15:55.917014

"""

# revision identifiers, used by Alembic.
revision = '6bbbf58ed9de'
down_revision = '82f4f4d14775'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('files', sa.Column('test_id',
                                     sa.String(36),
                                     sa.ForeignKey('tests.id',
                                                   ondelete='CASCADE'),
                                     nullable=True))
    pass


def downgrade():
    pass
