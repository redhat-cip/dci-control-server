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
revision = '4e45b2030162'
down_revision = '32fdbb3715e7'
branch_labels = None
depends_on = None

from alembic import op
from dci.db import models
from sqlalchemy import sql
from sqlalchemy import exc as sa_exc


def upgrade():
    db_conn = op.get_bind()
    _JUTR = models.JOIN_USERS_TEAMS_ROLES

    # get the epm team
    query = sql.select([models.TEAMS]).where(
        models.TEAMS.c.name == 'EPM'
    )
    team_epm = db_conn.execute(query).fetchone()
    if team_epm is None:
        return

    def get_users_ids_of_team(team_id):
        query = sql.select([_JUTR]).where(
            _JUTR.c.team_id == team_id)
        rows = db_conn.execute(query).fetchall()
        return [str(row.user_id) for row in rows]

    # get all products
    query = sql.select([models.PRODUCTS])
    all_products = db_conn.execute(query).fetchall()

    # for each product get the products users and insert them in the epm team
    for product in all_products:
        users_ids = get_users_ids_of_team(product.team_id)
        for user_id in users_ids:
            try:
                q = _JUTR.insert().values(
                    team_id=team_epm.id,
                    user_id=user_id,
                    role='EPM'
                )
                db_conn.execute(q)
            except sa_exc.IntegrityError:
                # if the user already exist, just ignore the statement
                pass


def downgrade():
    pass
