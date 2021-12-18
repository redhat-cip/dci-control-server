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

"""Add tags array to jobs

Revision ID: 45e44e338043
Revises: 49363052bd7d
Create Date: 2020-03-19 16:01:17.853976

"""

# revision identifiers, used by Alembic.
revision = "45e44e338043"
down_revision = "49363052bd7d"
branch_labels = None
depends_on = None
import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy import sql

from dci.db import models
from dci.common import utils


metadata = sa.MetaData()


TAGS = sa.Table(
    "tags",
    metadata,
    sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
    sa.Column(
        "created_at", sa.DateTime(), default=datetime.datetime.utcnow, nullable=False
    ),
    sa.Column("name", sa.String(40), nullable=False, unique=True),
    sa.Column(
        "etag",
        sa.String(40),
        nullable=False,
        default=utils.gen_etag,
        onupdate=utils.gen_etag,
    ),
)


JOIN_JOBS_TAGS = sa.Table(
    "jobs_tags",
    metadata,
    sa.Column(
        "tag_id",
        pg.UUID(as_uuid=True),
        sa.ForeignKey("tags.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    ),
    sa.Column(
        "job_id",
        pg.UUID(as_uuid=True),
        sa.ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    ),
)


def upgrade():
    db_conn = op.get_bind()
    op.add_column("jobs", sa.Column("tag", pg.ARRAY(sa.Text), default=[]))

    # get all the tags
    query = sql.select([TAGS])
    all_tags = db_conn.execute(query).fetchall()
    # associate tag id to their name
    all_tags_dict = {str(at.id): at.name for at in all_tags}

    # get all the jobs that are associated to tags
    query = sql.select([JOIN_JOBS_TAGS])
    jobs_tags = db_conn.execute(query).fetchall()
    jobs_to_tags = {}
    for j_t in jobs_tags:
        if jobs_to_tags.get(str(j_t.job_id)) is None:
            jobs_to_tags[str(j_t.job_id)] = [all_tags_dict[str(j_t.tag_id)]]
        else:
            jobs_to_tags[str(j_t.job_id)] += [all_tags_dict[str(j_t.tag_id)]]

    # update each job's tag column with their tags
    for j_t in jobs_tags:
        query = (
            models.JOBS.update()
            .where(models.JOBS.c.id == j_t.job_id)
            .values(tag=jobs_to_tags[str(j_t.job_id)])
        )
        db_conn.execute(query)


def downgrade():
    pass
