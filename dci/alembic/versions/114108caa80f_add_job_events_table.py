#
# Copyright (C) 2018 Red Hat, Inc
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

"""Add job_events table

Revision ID: 114108caa80f
Revises: 3cdd5a268c45
Create Date: 2018-04-26 15:58:41.676961

"""

# revision identifiers, used by Alembic.
revision = "114108caa80f"
down_revision = "3cdd5a268c45"
branch_labels = None
depends_on = None

from alembic import op
import datetime
from dci.db import models
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


def upgrade():

    op.drop_table("files_events")
    op.execute("DROP TYPE files_actions")
    op.create_table(
        "jobs_events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            default=datetime.datetime.utcnow,
            nullable=False,
        ),
        sa.Column("job_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("topic_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("status", models.FINAL_STATUSES_ENUM),
        sa.Index("jobs_events_job_id_idx", "job_id"),
    )


def downgrade():
    pass
