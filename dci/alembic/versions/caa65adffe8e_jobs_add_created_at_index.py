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

"""jobs_add_created_at_index

Revision ID: caa65adffe8e
Revises: 46dff7ed04c2
Create Date: 2023-06-23 01:31:49.194371

"""

# revision identifiers, used by Alembic.
revision = "caa65adffe8e"
down_revision = "46dff7ed04c2"
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.create_index("jobs_created_at_idx", "jobs", ["created_at"])


def downgrade():
    pass
