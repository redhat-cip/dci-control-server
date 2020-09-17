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

"""add state to issues

Revision ID: 6a224b67052
Revises: 358cdb161d55
Create Date: 2018-11-13 20:53:55.247713

"""

# revision identifiers, used by Alembic.
revision = "6a224b67052"
down_revision = "358cdb161d55"
branch_labels = None
depends_on = None

from dci.common import utils
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


RESOURCE_STATES = ["active", "inactive", "archived"]
STATES = sa.Enum(*RESOURCE_STATES, name="states")


def upgrade():
    op.add_column("issues", sa.Column("state", STATES, default="active"))
    op.add_column(
        "issues",
        sa.Column(
            "etag",
            sa.String(40),
            nullable=False,
            default=utils.gen_etag,
            onupdate=utils.gen_etag,
        ),
    )
    op.add_column(
        "issues",
        sa.Column(
            "topic_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("topics.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    # drop the unique contraint by removing and adding the column
    op.drop_column("issues", "url")
    op.add_column("issues", sa.Column("url", sa.Text))
    op.create_unique_constraint(
        constraint_name="issues_url_topic_id_key",
        table_name="issues",
        columns=["url", "topic_id"],
    )


def downgrade():
    pass
