#
# Copyright (C) 2019 Red Hat, Inc
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

"""add duration to jobs

Revision ID: 49363052bd7d
Revises: 5ad9b5342acf
Create Date: 2019-07-31 15:44:52.724198

"""

# revision identifiers, used by Alembic.
revision = "49363052bd7d"
down_revision = "5ad9b5342acf"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("jobs", sa.Column("duration", sa.Integer, default=0))


def downgrade():
    pass
