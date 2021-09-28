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

"""remove analytics

Revision ID: 61f71f157057
Revises: 27d3441e7641
Create Date: 2021-09-28 11:51:30.741652

"""

# revision identifiers, used by Alembic.
revision = "61f71f157057"
down_revision = "27d3441e7641"
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_table("analytics")


def downgrade():
    pass
