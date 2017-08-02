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

"""Add topic_id column in jobs

Revision ID: 5d48174e4f24
Revises: af7a9b76939b
Create Date: 2017-07-08 16:15:17.929962

"""

# revision identifiers, used by Alembic.
revision = '5d48174e4f24'
down_revision = 'af7a9b76939b'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy import sql
from sqlalchemy.dialects import postgresql as pg

from dci.common import exceptions as dci_exc
from dci.db import models


def upgrade():

    _JOBS = models.JOBS

    def _get_topic_id_from_jobdefinition(conn, j_id):
        query = (sql.select([models.JOBDEFINITIONS])
                 .where(models.JOBDEFINITIONS.c.id == j_id))
        row = conn.execute(query).fetchone()
        return row.topic_id

    db_conn = op.get_bind()
    with db_conn.begin():
        op.add_column('jobs',
                      sa.Column('topic_id', pg.UUID(as_uuid=True),
                                sa.ForeignKey('topics.id', ondelete='CASCADE'),
                                # Will be False when jobdefinition will be
                                # removed
                                nullable=True))
        op.create_index('jobs_topic_id_idx', 'jobs', ['topic_id'])

        # for each job, update its topic_id field
        query = sql.select([models.JOBS.c.id, models.JOBS.c.jobdefinition_id])
        all_jobs = db_conn.execute(query).fetchall()

        for j in all_jobs:
            job = dict(j)
            topic_id = _get_topic_id_from_jobdefinition(db_conn,
                                                        job['jobdefinition_id'])  # noqa
            values = {'topic_id': topic_id}
            query = _JOBS.update().where(_JOBS.c.id == job['id']). \
                values(**values)
            result = db_conn.execute(query)
            if not result.rowcount:
                raise dci_exc.DCIException('Failed to update job %s'
                                           % job['id'])


def downgrade():
    pass
