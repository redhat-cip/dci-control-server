#
# Copyright (C) 2019 Red Hat, Inc
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

"""adds_secondary_topic_to_jobs

Revision ID: 2850e054d9f0
Revises: 22666e71ab8d
Create Date: 2019-02-11 22:31:55.984866

"""

# revision identifiers, used by Alembic.
revision = "2850e054d9f0"
down_revision = "22666e71ab8d"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


def upgrade():
    op.add_column(
        "jobs",
        sa.Column(
            "topic_id_secondary",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("topics.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )


def downgrade():
    pass
