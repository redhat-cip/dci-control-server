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

"""remove key value indexes

Revision ID: 667206af3c8b
Revises: 1c16157d0b73
Create Date: 2023-06-08 18:50:35.572374

"""

# revision identifiers, used by Alembic.
revision = "667206af3c8b"
down_revision = "1c16157d0b73"
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_index("jobs_keys_values_job_id_idx", table_name="jobs_keys_values")
    op.drop_index("jobs_keys_values_key_idx", table_name="jobs_keys_values")
    op.drop_table("jobs_keys_values")


def downgrade():
    pass
