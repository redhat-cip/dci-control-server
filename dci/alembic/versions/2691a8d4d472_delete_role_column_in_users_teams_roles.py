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

"""Delete role column in users_teams_roles

Revision ID: 2691a8d4d472
Revises: 4e45b2030162
Create Date: 2019-06-20 08:08:47.495358

"""

# revision identifiers, used by Alembic.
revision = "2691a8d4d472"
down_revision = "4e45b2030162"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column("users_teams_roles", "role")


def downgrade():
    op.add_column(
        "users_teams_roles",
        sa.Column("role", sa.String(255), default="USER", nullable=False),
    )
