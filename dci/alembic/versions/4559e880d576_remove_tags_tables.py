#
# Copyright (C) 2021 Red Hat, Inc
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

"""Remove tags tables

Revision ID: 4559e880d576
Revises: 61f71f157057
Create Date: 2021-11-22 13:56:18.820990

"""

# revision identifiers, used by Alembic.
revision = "4559e880d576"
down_revision = "61f71f157057"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.drop_table("components_tags")
    op.drop_table("jobs_tags")
    op.drop_table("tags")


def downgrade():
    op.create_table(
        "jobs_tags",
        sa.Column("tag_id", postgresql.UUID(), autoincrement=False, nullable=False),
        sa.Column("job_id", postgresql.UUID(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["job_id"], [u"jobs.id"], name=u"jobs_tags_job_id_fkey", ondelete=u"CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"], [u"tags.id"], name=u"jobs_tags_tag_id_fkey", ondelete=u"CASCADE"
        ),
        sa.PrimaryKeyConstraint("tag_id", "job_id", name=u"jobs_tags_pkey"),
    )
    op.create_table(
        "components_tags",
        sa.Column("tag_id", postgresql.UUID(), autoincrement=False, nullable=False),
        sa.Column(
            "component_id", postgresql.UUID(), autoincrement=False, nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["component_id"],
            [u"components.id"],
            name=u"components_tags_component_id_fkey",
            ondelete=u"CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"],
            [u"tags.id"],
            name=u"components_tags_tag_id_fkey",
            ondelete=u"CASCADE",
        ),
        sa.PrimaryKeyConstraint("tag_id", "component_id", name=u"components_tags_pkey"),
    )
    op.create_table(
        "tags",
        sa.Column("id", postgresql.UUID(), autoincrement=False, nullable=False),
        sa.Column(
            "created_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False
        ),
        sa.Column("name", sa.VARCHAR(length=40), autoincrement=False, nullable=False),
        sa.Column("etag", sa.VARCHAR(length=40), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint("id", name=u"tags_pkey"),
        sa.UniqueConstraint("name", name=u"tags_name_key"),
    )
