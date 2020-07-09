#
# Copyright (C) 2020 Red Hat, Inc
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

"""added a kind field in components

Revision ID: 4956a84ad8e
Revises: 1f29092c3fe
Create Date: 2020-07-09 18:18:30.708807

"""

# revision identifiers, used by Alembic.
revision = '4956a84ad8e'
down_revision = '1f29092c3fe'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('components', sa.Column('kind', sa.String(255)))


def downgrade():
    pass
