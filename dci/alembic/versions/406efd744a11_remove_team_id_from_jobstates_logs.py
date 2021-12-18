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

"""remove_team_id_from_jobstates_logs

Revision ID: 406efd744a11
Revises: 1a86396beec0
Create Date: 2019-01-29 15:34:53.763827

"""

# revision identifiers, used by Alembic.
revision = "406efd744a11"
down_revision = "1a86396beec0"
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_index("jobstates_team_id_idx", table_name="jobstates")
    op.drop_column("jobstates", "team_id")

    op.drop_index("logs_team_id_idx", table_name="logs")
    op.drop_column("logs", "team_id")

    op.drop_column("feeders", "role_id")


def downgrade():
    pass
