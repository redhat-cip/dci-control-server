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

"""move read only users to redhat team

Revision ID: 32fdbb3715e7
Revises: 3eccf653cd30
Create Date: 2019-06-10 03:39:11.655275

"""

# revision identifiers, used by Alembic.
revision = '32fdbb3715e7'
down_revision = '3eccf653cd30'
branch_labels = None
depends_on = None

from alembic import op
from dci.db import models
from sqlalchemy import exc as sa_exc
from sqlalchemy import sql


def upgrade():
    db_conn = op.get_bind()

    # get the Red Hat team
    query = sql.select([models.TEAMS]).where(
        models.TEAMS.c.name == 'Red Hat'
    )
    team_redhat = db_conn.execute(query).fetchone()
    if team_redhat is None:
        return

    # get all the read only users
    _JUTR = models.JOIN_USERS_TEAMS_ROLES
    query = sql.select([_JUTR]).where(
        sql.and_(
            _JUTR.c.team_id == None,   # noqa
            _JUTR.c.role == 'READ_ONLY_USER'
    ))
    users_teams_roles = db_conn.execute(query).fetchall()

    # add the users to the Red Hat team
    for utr in users_teams_roles:
        try:
            q = _JUTR.insert().values(team_id=team_redhat.id,
                                      user_id=utr.user_id,
                                      role='READ_ONLY_USER')
            db_conn.execute(q)
        except sa_exc.IntegrityError:
            # if the user already exist, just ignore the statement
            pass


def downgrade():
    pass
