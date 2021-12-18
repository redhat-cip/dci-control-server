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

"""delete meta

Revision ID: 22666e71ab8d
Revises: 3b7aaa1c90da
Create Date: 2019-01-28 09:37:04.488271

"""

# revision identifiers, used by Alembic.
revision = "22666e71ab8d"
down_revision = "3b7aaa1c90da"
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_table("metas")


def downgrade():
    pass
