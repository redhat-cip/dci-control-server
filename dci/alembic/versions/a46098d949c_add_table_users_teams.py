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
revision = 'a46098d949c'
down_revision = '192940556583'
branch_labels = None
depends_on = None


from alembic import op
import sqlalchemy as sa
from sqlalchemy import sql
from sqlalchemy.dialects import postgresql
from dci.db import models


def upgrade():
    op.create_table(
        "users_teams",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.UniqueConstraint("user_id", "team_id", name="users_teams_key"),
    )
    db_conn = op.get_bind()
    users_teams_roles = db_conn.execute(
        sql.select([models.JOIN_USERS_TEAMS_ROLES])
    ).fetchall()
    for user_team in users_teams_roles:
        db_conn.execute(
            models.JOIN_USERS_TEAMS.insert().values(
                user_id=user_team["users_id"], team_id=user_team["team_id"]
            )
        )


def downgrade():
    pass
