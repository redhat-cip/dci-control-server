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

"""AddCounter

Revision ID: eba69907de79
Revises: 114108caa80f
Create Date: 2018-05-07 15:34:42.487198

"""

# revision identifiers, used by Alembic.
revision = "eba69907de79"
down_revision = "114108caa80f"
branch_labels = None
depends_on = None

from alembic import op
import datetime
import sqlalchemy as sa

from dci.common import utils


def upgrade():
    op.create_table(
        "counter",
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
        sa.Column("name", sa.String(255), primary_key=True, nullable=False),
        sa.Column("sequence", sa.Integer, default=0),
        sa.Column(
            "etag",
            sa.String(40),
            nullable=False,
            default=utils.gen_etag,
            onupdate=utils.gen_etag,
        ),
    )


def downgrade():
    pass
