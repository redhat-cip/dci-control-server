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

"""ScheduleUpdateJob

Revision ID: d94013e874ab
Revises: b0436aece81f
Create Date: 2018-03-06 13:40:48.079028

"""

# revision identifiers, used by Alembic.
revision = "d94013e874ab"
down_revision = "b0436aece81f"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


def upgrade():
    op.add_column(
        "jobs",
        sa.Column(
            "update_previous_job_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id"),
            nullable=True,
            default=None,
        ),
    )
    op.create_index(
        "jobs_update_previous_job_id_idx", "jobs", ["update_previous_job_id"]
    )


def downgrade():
    pass
