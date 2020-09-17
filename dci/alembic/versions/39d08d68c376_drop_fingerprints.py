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

"""drop_fingerprints

Revision ID: 39d08d68c376
Revises: b4a4e3568d82
Create Date: 2018-07-06 12:42:04.354901

"""

# revision identifiers, used by Alembic.
revision = "39d08d68c376"
down_revision = "b4a4e3568d82"
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_table("fingerprints")


def downgrade():
    pass
