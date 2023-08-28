#
# Copyright (C) 2023 Red Hat, Inc
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

"""add has_pre_release_access to team

Revision ID: 850229f38182
Revises: 5b771c01636f
Create Date: 2023-08-28 10:18:10.633247

"""

# revision identifiers, used by Alembic.
revision = "850229f38182"
down_revision = "5b771c01636f"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        "teams",
        sa.Column(
            "has_pre_release_access",
            sa.BOOLEAN(),
            server_default="false",
            nullable=False,
        ),
    )


def downgrade():
    op.drop_column("teams", "has_pre_release_access")
