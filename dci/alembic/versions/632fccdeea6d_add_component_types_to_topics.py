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

import datetime
from dci.common import exceptions as dci_exc
from dci.common import utils
from dci.db import models


JOBDEFINITIONS = sa.Table(
    'jobdefinitions', sa.MetaData(),
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
    sa.Column('name', sa.String(255)),
    sa.Column('topic_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('topics.id', ondelete='CASCADE'),
              nullable=True),
    sa.Index('jobdefinitions_topic_id_idx', 'topic_id'),
    sa.Column('comment', sa.Text),
    sa.Column('component_types', pg.JSON, default=[]),
)


def upgrade():
    op.add_column('topics', sa.Column('component_types', pg.JSON, default=[]))

    # There is only one jobdefinition per topic so let's move the
    # component_types of each jobdefinition into the associated topic
    db_conn = op.get_bind()
    _TOPICS = models.TOPICS

    with db_conn.begin():
        # get all jobdefinitions
        query = sql.select([JOBDEFINITIONS])
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
