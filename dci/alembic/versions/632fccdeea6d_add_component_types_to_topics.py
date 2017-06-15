#
# Copyright (C) 2017 Red Hat, Inc
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

"""add component_types to topics

Revision ID: 632fccdeea6d
Revises: 9b80c710510c
Create Date: 2017-06-15 04:12:44.989983

"""

# revision identifiers, used by Alembic.
revision = '632fccdeea6d'
down_revision = '9b80c710510c'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy import sql

from dci.common import exceptions as dci_exc
from dci.db import models


def upgrade():
    op.add_column('topics', sa.Column('component_types', pg.JSON, default=[]))

    # There is only one jobdefinition per topic so let's move the
    # component_types of each jobdefinition into the associated topic
    db_conn = op.get_bind()
    _TOPICS = models.TOPICS

    with db_conn.begin():
        # get all jobdefinitions
        query = sql.select([models.JOBDEFINITIONS])
        all_jobdefinitions = db_conn.execute(query).fetchall()
        # for each jobdefinitions move copy its component_types into its
        # associated topic
        for j in all_jobdefinitions:
            jd = dict(j)
            values = {'component_types': jd['component_types']}
            query = _TOPICS.update().where(_TOPICS.c.id == jd['topic_id']).\
                values(**values)
            result = db_conn.execute(query)
            if not result.rowcount:
                raise dci_exc.DCIException('Failed to update topic %s'
                                           % jd['topic_id'])


def downgrade():
    pass
