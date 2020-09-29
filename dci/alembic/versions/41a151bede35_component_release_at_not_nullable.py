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

"""component release_at not nullable

Revision ID: 41a151bede35
Revises: 26cfed00671
Create Date: 2020-09-29 22:04:39.730229

"""

# revision identifiers, used by Alembic.
revision = '41a151bede35'
down_revision = '26cfed00671'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('components', 'release_at', nullable=False)


def downgrade():
    pass
