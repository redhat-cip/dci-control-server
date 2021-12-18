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

"""move users to users_teams_role

Revision ID: 1a86396beec0
Revises: 4c70cf0e4637
Create Date: 2019-02-25 16:23:23.534726

"""

# revision identifiers, used by Alembic.
revision = "1a86396beec0"
down_revision = "4c70cf0e4637"
branch_labels = None
depends_on = None

from dci.db import models
from dci.common import utils

from alembic import op
import sqlalchemy as sa
from sqlalchemy import sql
from sqlalchemy.dialects import postgresql as pg


def upgrade():
    db_conn = op.get_bind()
    metadata = sa.MetaData()

    # users role_id will be removed so we use kind of closure to not
    # break the upcoming migrations
    _USERS = sa.Table(
        "users",
        metadata,
        sa.Column(
            "id", pg.UUID(as_uuid=True), primary_key=True, default=utils.gen_uuid
        ),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column(
            "role_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("roles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "team_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )

    # roles table will be removed so we use kind of closure to not
    # break the upcoming migrations
    _ROLES = sa.Table(
        "roles",
        metadata,
        sa.Column(
            "id", pg.UUID(as_uuid=True), primary_key=True, default=utils.gen_uuid
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
    )

    get_all_users = sql.select([_USERS, _ROLES], use_labels=True).select_from(
        _USERS.join(_ROLES, _ROLES.c.id == _USERS.c.role_id)
    )

    all_users = db_conn.execute(get_all_users).fetchall()

    with db_conn.begin():
        for user in all_users:
            current_role = user["roles_label"]
            # ADMIN role will be removed and turned to regular USER role
            if current_role == "ADMIN":
                current_role = "USER"
            db_conn.execute(
                models.JOIN_USERS_TEAMS_ROLES.insert().values(
                    user_id=user["users_id"],
                    team_id=user["users_team_id"],
                    role=current_role,
                )
            )


def downgrade():
    pass
