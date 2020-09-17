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

"""Add topics export control

Revision ID: 406a6d793f29
Revises: b71a4139c14f
Create Date: 2018-09-12 11:56:54.602128

"""

# revision identifiers, used by Alembic.
revision = "406a6d793f29"
down_revision = "b71a4139c14f"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        "topics",
        sa.Column(
            "export_control",
            sa.BOOLEAN,
            nullable=False,
            default=False,
            server_default="false",
        ),
    )


def downgrade():
    pass
