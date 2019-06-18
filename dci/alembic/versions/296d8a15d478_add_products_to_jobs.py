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

"""add products to jobs

Revision ID: 296d8a15d478
Revises: 236e3b2c2a3d
Create Date: 2019-06-18 15:58:20.213113

"""

# revision identifiers, used by Alembic.
revision = '296d8a15d478'
down_revision = '236e3b2c2a3d'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy import sql
from sqlalchemy.dialects import postgresql as pg
from dci.db import models


def upgrade():
    db_conn = op.get_bind()
    op.add_column('jobs',
                  sa.Column('product_id', pg.UUID(as_uuid=True),
                            sa.ForeignKey('products.id', ondelete='CASCADE'),
                            nullable=True))
    op.create_index('jobs_product_id_idx', 'jobs',
                    ['product_id'])

    # get all the jobs
    query = sql.select([models.JOBS])
    jobs = db_conn.execute(query).fetchall()

    def get_product_id(topic_id):
        query = sql.select([models.TOPICS]).where(
            models.TOPICS.c.id == job.topic_id)
        topic = db_conn.execute(query).fetchone()
        return topic.product_id

    cache_topic_id_to_product_id = {}
    for job in jobs:
        if str(job.topic_id) not in cache_topic_id_to_product_id.keys():
            product_id = get_product_id(job.topic_id)
            cache_topic_id_to_product_id[str(job.topic_id)] = product_id
        product_id = cache_topic_id_to_product_id[str(job.topic_id)]
        query = models.JOBS.update().where(
            models.JOBS.c.id == job.id).values(product_id=product_id)
        db_conn.execute(query)


def downgrade():
    pass
