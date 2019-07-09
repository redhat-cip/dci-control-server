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

"""Add table users teams

Revision ID: a46098d949c
Revises: 192940556583
Create Date: 2019-07-05 07:06:42.730551

"""

# revision identifiers, used by Alembic.
revision = "a46098d949c"
down_revision = "192940556583"
branch_labels = None
depends_on = None


from alembic import op


def upgrade():
    op.drop_column("users_teams_roles", "role")
    op.drop_constraint(
        table_name="users_teams_roles", constraint_name="users_teams_roles_key"
    )
    op.rename_table("users_teams_roles", "users_teams")
    op.create_unique_constraint(
        constraint_name="users_teams_key",
        table_name="users_teams",
        columns=["user_id", "team_id"],
    )


def downgrade():
    pass
