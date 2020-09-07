#
# Copyright (C) 2020 Red Hat, Inc
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

"""add release_date to components

Revision ID: 26cfed00671
Revises: 2a66d59901a
Create Date: 2020-09-29 12:45:37.073362

"""

# revision identifiers, used by Alembic.
revision = '26cfed00671'
down_revision = '2a66d59901a'
branch_labels = None
depends_on = None

from alembic import op
import datetime
from dci.db import models
import sqlalchemy as sa
from sqlalchemy import sql


def upgrade():
    db_conn = op.get_bind()
    op.add_column('components', sa.Column('release_at', sa.DateTime(),
                  default=datetime.datetime.utcnow, nullable=True))

    query = sql.select([models.COMPONENTS])
    components = db_conn.execute(query).fetchall()

    for c in components:
        query = models.COMPONENTS.update().where(models.COMPONENTS.c.id == c.id).\
            values(release_at=c.created_at)
        db_conn.execute(query)


def downgrade():
    pass
