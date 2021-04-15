#
# Copyright (C) 2021 Red Hat, Inc
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

"""Add job_id index on jobs_components table

Revision ID: 403af034dd2f
Revises: 4509202d08ea
Create Date: 2021-04-15 12:13:14.349922

"""

# revision identifiers, used by Alembic.
revision = "403af034dd2f"
down_revision = "4509202d08ea"
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.create_index(
        "jobs_components_job_id_idx", "jobs_components", ["job_id"], unique=False
    )


def downgrade():
    op.drop_index("jobs_components_job_id_idx", table_name="jobs_components")
