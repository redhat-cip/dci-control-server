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

"""remove_next_topic

Revision ID: d7d29a66aac5
Revises: 772428482e52
Create Date: 2018-07-03 11:31:10.379341

"""

# revision identifiers, used by Alembic.
revision = "d7d29a66aac5"
down_revision = "772428482e52"
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_column("topics", "next_topic")


def downgrade():
    pass
