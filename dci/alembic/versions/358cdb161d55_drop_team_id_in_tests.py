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

"""drop team_id in tests

Revision ID: 358cdb161d55
Revises: e06d36c55bfe
Create Date: 2018-11-06 23:57:49.552606

"""

# revision identifiers, used by Alembic.
revision = "358cdb161d55"
down_revision = "e06d36c55bfe"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


def upgrade():
    op.drop_column("tests", "team_id")
    op.drop_column("tests", "name")
    op.add_column("tests", sa.Column("name", sa.Text, nullable=False, unique=True))
    op.drop_table("remoteci_tests")
    op.drop_table("topic_tests")
    op.create_table(
        "issues_tests",
        sa.Column(
            "issue_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("issues.id", ondelete="CASCADE"),
            nullable=False,
            primary_key=True,
        ),
        sa.Column(
            "test_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("tests.id", ondelete="CASCADE"),
            nullable=False,
            primary_key=True,
        ),
    )


def downgrade():
    pass
