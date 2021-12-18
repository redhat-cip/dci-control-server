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

"""Add analytics

Revision ID: 46fa9eb61235
Revises: bcd903a35145
Create Date: 2018-08-10 13:51:24.538380

"""

# revision identifiers, used by Alembic.
revision = "46fa9eb61235"
down_revision = "bcd903a35145"
branch_labels = None
depends_on = None

import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
import sqlalchemy_utils as sa_utils

from dci.common import utils


def upgrade():

    op.create_table(
        "analytics",
        sa.Column(
            "id", pg.UUID(as_uuid=True), primary_key=True, default=utils.gen_uuid
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            default=datetime.datetime.utcnow,
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            onupdate=datetime.datetime.utcnow,
            default=datetime.datetime.utcnow,
            nullable=False,
        ),
        sa.Column(
            "etag",
            sa.String(40),
            nullable=False,
            default=utils.gen_etag,
            onupdate=utils.gen_etag,
        ),
        sa.Column(
            "team_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Index("analytics_team_id_idx", "team_id"),
        sa.Column(
            "job_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Index("analytics_job_id_idx", "job_id"),
        sa.Column("type", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), unique=False, nullable=False),
        sa.Index("analytics_name_team_id_idx", "name", "team_id", unique=True),
        sa.Column("url", sa.String(255)),
        sa.Column("data", sa_utils.JSONType, default={}, nullable=False),
    )


def downgrade():
    pass
