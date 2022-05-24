#
# Copyright (C) 2022 Red Hat, Inc
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

"""addPipelineIdInJobs

Revision ID: fd04b7d20477
Revises: ab48aca06ac4
Create Date: 2022-05-27 16:16:51.000039

"""

# revision identifiers, used by Alembic.
revision = "fd04b7d20477"
down_revision = "ab48aca06ac4"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


def upgrade():
    op.add_column(
        "jobs",
        sa.Column(
            "pipeline_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("pipelines.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )


def downgrade():
    pass
