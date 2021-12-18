#
# Copyright (C) 2021 Red Hat, Inc
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

"""add job meta value

Revision ID: 27d3441e7641
Revises: 4509202d08ea
Create Date: 2021-05-20 14:53:28.478095

"""

# revision identifiers, used by Alembic.
revision = "27d3441e7641"
down_revision = "4509202d08ea"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("jobs", sa.Column("status_reason", sa.Text))
    op.add_column("jobs", sa.Column("configuration", sa.Text))
    op.add_column("jobs", sa.Column("name", sa.Text))
    op.add_column("jobs", sa.Column("url", sa.Text))


def downgrade():
    pass
