#
# Copyright (C) 2024 Red Hat, Inc
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

"""Drop topic team association

Revision ID: 4ff34474b4fd
Revises: 83c6c24dc160
Create Date: 2024-05-28 07:21:35.614709

"""

# revision identifiers, used by Alembic.
revision = "4ff34474b4fd"
down_revision = "83c6c24dc160"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.drop_table("topics_teams")


def downgrade():
    op.create_table(
        "topics_teams",
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["team_id"],
            ["teams.id"],
            name="topics_teams_team_id_fkey",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["topics.id"],
            name="topics_teams_topic_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("topic_id", "team_id", name="topics_teams_pkey"),
    )
