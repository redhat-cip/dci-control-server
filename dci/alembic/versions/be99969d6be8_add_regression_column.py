#
# Copyright (C) 2018 Red Hat, Inc
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

"""add regression column

Revision ID: be99969d6be8
Revises: 8e1349eb050b
Create Date: 2018-01-09 12:24:21.289668

"""

# revision identifiers, used by Alembic.
revision = 'be99969d6be8'
down_revision = '8e1349eb050b'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils as sa_utils


def upgrade():
    op.add_column('tests_results',
                  sa.Column('regressions', sa_utils.JSONType))


def downgrade():
    pass
