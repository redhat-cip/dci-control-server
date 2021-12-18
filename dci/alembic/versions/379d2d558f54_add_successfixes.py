#
# Copyright (C) Red Hat, Inc
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

"""add successfixes

Revision ID: 379d2d558f54
Revises: 6a224b67052
Create Date: 2018-11-23 17:18:44.505943

"""

# revision identifiers, used by Alembic.
revision = "379d2d558f54"
down_revision = "6a224b67052"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("tests_results", sa.Column("successfixes", sa.Integer, default=0))


def downgrade():
    pass
