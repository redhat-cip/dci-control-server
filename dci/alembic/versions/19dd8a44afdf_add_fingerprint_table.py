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

"""Add fingerprint table

Revision ID: 19dd8a44afdf
Revises: 8e1349eb050b
Create Date: 2017-08-01 11:00:54.851361

"""

# revision identifiers, used by Alembic.
revision = "19dd8a44afdf"
down_revision = "8e1349eb050b"
branch_labels = None
depends_on = None

import datetime
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils as sa_utils
from sqlalchemy.dialects import postgresql as pg

from dci.common import utils

RESOURCE_STATES = ["active", "inactive", "archived"]
STATES = sa.Enum(*RESOURCE_STATES, name="states")


def upgrade():
    states = pg.ENUM("active", "inactive", "archived", name="states", create_type=False)

    op.create_table(
        "fingerprints",
        sa.Column(
            "id", pg.UUID(as_uuid=True), primary_key=True, default=utils.gen_uuid
        ),
        sa.Column("name", sa.String(255), nullable=False),
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
            "topic_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("topics.id", ondelete="CASCADE"),
            nullable=False,
            primary_key=True,
        ),
        sa.Column("fingerprint", sa_utils.JSONType, nullable=False),
        sa.Column("actions", sa_utils.JSONType, nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("state", states, default="active"),
    )


def downgrade():
    pass
