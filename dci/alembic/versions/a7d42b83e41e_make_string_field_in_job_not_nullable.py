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

"""Make string field in job not nullable

Revision ID: a7d42b83e41e
Revises: 36c753d31b62
Create Date: 2024-01-23 10:37:18.724242

"""

# revision identifiers, used by Alembic.
revision = "a7d42b83e41e"
down_revision = "36c753d31b62"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column(
        "jobs",
        "client_version",
        existing_type=sa.VARCHAR(length=255),
        nullable=False,
        existing_server_default="",
    )
    op.alter_column(
        "jobs",
        "comment",
        existing_type=sa.TEXT(),
        nullable=False,
        existing_server_default="",
    )
    op.alter_column(
        "jobs",
        "configuration",
        existing_type=sa.TEXT(),
        nullable=False,
        existing_server_default="",
    )
    op.alter_column(
        "jobs",
        "name",
        existing_type=sa.TEXT(),
        nullable=False,
        existing_server_default="",
    )
    op.alter_column(
        "jobs",
        "status_reason",
        existing_type=sa.TEXT(),
        nullable=False,
        existing_server_default="",
    )
    op.alter_column(
        "jobs",
        "url",
        existing_type=sa.TEXT(),
        nullable=False,
        existing_server_default="",
    )
    op.alter_column(
        "jobs",
        "user_agent",
        existing_type=sa.VARCHAR(length=255),
        nullable=False,
        existing_server_default="",
    )


def downgrade():
    op.alter_column(
        "jobs",
        "user_agent",
        existing_type=sa.VARCHAR(length=255),
        nullable=True,
        existing_server_default="",
    )
    op.alter_column(
        "jobs",
        "url",
        existing_type=sa.TEXT(),
        nullable=True,
        existing_server_default="",
    )
    op.alter_column(
        "jobs",
        "status_reason",
        existing_type=sa.TEXT(),
        nullable=True,
        existing_server_default="",
    )
    op.alter_column(
        "jobs",
        "name",
        existing_type=sa.TEXT(),
        nullable=True,
        existing_server_default="",
    )
    op.alter_column(
        "jobs",
        "configuration",
        existing_type=sa.TEXT(),
        nullable=True,
        existing_server_default="",
    )
    op.alter_column(
        "jobs",
        "comment",
        existing_type=sa.TEXT(),
        nullable=True,
        existing_server_default="",
    )
    op.alter_column(
        "jobs",
        "client_version",
        existing_type=sa.VARCHAR(length=255),
        nullable=True,
        existing_server_default="",
    )
