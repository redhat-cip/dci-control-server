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

"""add_rh_role_employee

Revision ID: 3750c0221184
Revises: d94013e874ab
Create Date: 2018-03-20 00:48:16.985829

"""

# revision identifiers, used by Alembic.
revision = "3750c0221184"
down_revision = "d94013e874ab"
branch_labels = None
depends_on = None

from dci.db import models
from dci.common import utils

from alembic import op
import datetime
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


def upgrade():
    db_conn = op.get_bind()
    metadata = sa.MetaData()
    ROLES = sa.Table(
        "roles",
        metadata,
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
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.UniqueConstraint("label", name="roles_label_key"),
        sa.Column("state", models.STATES, default="active"),
    )

    read_only_user_role = {
        "name": "Read only user",
        "label": "READ_ONLY_USER",
        "description": "User with RO access",
    }

    query = ROLES.insert().values(**read_only_user_role)
    db_conn.execute(query)


def downgrade():
    pass
