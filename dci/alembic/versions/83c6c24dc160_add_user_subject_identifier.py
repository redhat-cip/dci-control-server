#
# Copyright (C) 2024 Red Hat, Inc
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

"""add user subject identifier

Revision ID: 83c6c24dc160
Revises: a7d42b83e41e
Create Date: 2024-02-19 11:22:26.083076

"""

# revision identifiers, used by Alembic.
revision = "83c6c24dc160"
down_revision = "a7d42b83e41e"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("users", sa.Column("sso_sub", sa.String(length=255), nullable=True))
    op.create_unique_constraint("users_sso_sub_key", "users", ["sso_sub"])


def downgrade():
    op.drop_constraint("users_sso_sub_key", "users", type_="unique")
    op.drop_column("users", "sso_sub")
