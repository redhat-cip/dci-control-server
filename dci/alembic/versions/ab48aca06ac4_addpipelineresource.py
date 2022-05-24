#
# Copyright (C) 2022 Red Hat, Inc
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

"""addPipelineResource

Revision ID: ab48aca06ac4
Revises: a39240b87069
Create Date: 2022-05-24 23:28:35.658856

"""

# revision identifiers, used by Alembic.
revision = "ab48aca06ac4"
down_revision = "a918b053c43a"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

import datetime
from dci.common import utils


def upgrade():
    RESOURCE_STATES = ["active", "inactive", "archived"]
    STATES = sa.Enum(*RESOURCE_STATES, name="states")

    op.create_table(
        "pipelines",
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
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("state", STATES, default="active"),
    )


def downgrade():
    pass
