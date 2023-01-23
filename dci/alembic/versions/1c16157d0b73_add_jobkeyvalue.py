#
# Copyright (C) 2023 Red Hat, Inc
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

"""Add JobKeyValue

Revision ID: 1c16157d0b73
Revises: 609db7251b15
Create Date: 2023-01-25 13:37:09.897416

"""

# revision identifiers, used by Alembic.
revision = "1c16157d0b73"
down_revision = "609db7251b15"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


def upgrade():
    op.create_table(
        "jobs_keys_values",
        sa.Column("key", sa.String(255), nullable=False, primary_key=True),
        sa.Column("value", sa.Float(), nullable=False, primary_key=True),
        sa.Column(
            "job_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id", ondelete="CASCADE"),
            nullable=False,
            primary_key=True,
        ),
    )
    op.create_index("jobs_keys_values_key_idx", "jobs_keys_values", ["key"])
    op.create_index("jobs_keys_values_job_id_idx", "jobs_keys_values", ["job_id"])


def downgrade():
    pass
