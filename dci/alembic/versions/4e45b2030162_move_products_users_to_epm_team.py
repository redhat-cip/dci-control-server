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

"""move products users to epm team

Revision ID: 4e45b2030162
Revises: 32fdbb3715e7
Create Date: 2019-06-11 18:46:40.929808

"""

# revision identifiers, used by Alembic.
revision = "4e45b2030162"
down_revision = "32fdbb3715e7"
branch_labels = None
depends_on = None

from alembic import op
from dci.db import models
from sqlalchemy import sql
from sqlalchemy import exc as sa_exc


def upgrade():
    db_conn = op.get_bind()
    query = sql.select([models.TEAMS]).where(models.TEAMS.c.name == "EPM")
    team_epm = db_conn.execute(query).fetchone()
    if team_epm is None:
        return

    def get_users_ids_of_team(team_id):
        query = sql.select([models.JOIN_USERS_TEAMS_ROLES]).where(
            models.JOIN_USERS_TEAMS_ROLES.c.team_id == team_id
        )
        rows = db_conn.execute(query).fetchall()
        return [row.user_id for row in rows]

    epms = {}
    query = sql.select([models.PRODUCTS]).where(models.PRODUCTS.c.state == "active")
    all_products = db_conn.execute(query).fetchall()
    for product in all_products:
        for user_id in get_users_ids_of_team(product.team_id):
            epms[str(user_id)] = {
                "team_id": team_epm.id,
                "user_id": user_id,
                "role": "EPM",
            }
    for epm in epms.values():
        query = sql.select([models.JOIN_USERS_TEAMS_ROLES]).where(
            sql.and_(
                models.JOIN_USERS_TEAMS_ROLES.c.team_id == epm["team_id"],
                models.JOIN_USERS_TEAMS_ROLES.c.user_id == epm["user_id"],
            )
        )
        _epm = db_conn.execute(query).fetchone()
        if _epm is None:
            db_conn.execute(
                models.JOIN_USERS_TEAMS_ROLES.insert().values(
                    team_id=epm["team_id"], user_id=epm["user_id"], role=epm["role"]
                )
            )


def downgrade():
    pass
