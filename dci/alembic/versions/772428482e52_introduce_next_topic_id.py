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

"""introduce_next_topic_id

Revision ID: 772428482e52
Revises: 39d08d68c376
Create Date: 2018-07-03 11:04:10.856837

"""

# revision identifiers, used by Alembic.
revision = "772428482e52"
down_revision = "39d08d68c376"
branch_labels = None
depends_on = None

from alembic import op
from sqlalchemy.dialects import postgresql as pg

import sqlalchemy as sa


def upgrade():
    op.add_column(
        "topics",
        sa.Column(
            "next_topic_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("topics.id"),
            nullable=True,
            default=None,
        ),
    )
    op.create_index("topics_next_topic_id_idx", "topics", ["next_topic_id"])
    op.execute("UPDATE topics SET next_topic_id = next_topic")


def downgrade():
    pass
