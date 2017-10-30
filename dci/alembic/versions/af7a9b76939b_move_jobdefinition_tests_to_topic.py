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

"""Move jobdefinition tests to topic

Revision ID: af7a9b76939b
Revises: 2db837be418a
Create Date: 2017-07-08 15:45:18.714525

"""

# revision identifiers, used by Alembic.
revision = 'af7a9b76939b'
down_revision = '2db837be418a'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy import sql

import datetime
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
    # There is only one jobdefinition per topic so let's move the
    # tests of each jobdefinition into the associated topic
    db_conn = op.get_bind()
    _JTT = models.JOIN_TOPICS_TESTS

    def _get_all_jobdefinitions_tests_ids(conn, jd_id):
        JDC = models.JOIN_JOBDEFINITIONS_TESTS
        query = (sql.select([models.TESTS.c.id])
                 .select_from(JDC.join(models.TESTS))
                 .where(JDC.c.jobdefinition_id == jd_id))
        rows = conn.execute(query)
        if rows:
            return list(rows)
        else:
            return []

    with db_conn.begin():
        # get all jobdefinitions
        query = sql.select([JOBDEFINITIONS])
        all_jobdefinitions = db_conn.execute(query).fetchall()
        # for each jobdefinitions copy its tests into its
        # associated topic
        for j in all_jobdefinitions:
            jd = dict(j)
            tests_ids = _get_all_jobdefinitions_tests_ids(db_conn, jd['id'])
            for t_id in tests_ids:
                values = {'topic_id': jd['topic_id'],
                          'test_id': t_id['id']}
                db_conn.execute(_JTT.insert().values(**values))

    op.alter_column('jobs', 'jobdefinition_id', nullable=True)


def downgrade():
    pass
