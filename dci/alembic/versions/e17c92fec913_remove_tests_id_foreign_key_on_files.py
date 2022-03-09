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

"""Remove tests id foreign key on files

Revision ID: e17c92fec913
Revises: 980e18983453
Create Date: 2022-03-09 07:58:39.842378

"""

# revision identifiers, used by Alembic.
revision = "e17c92fec913"
down_revision = "980e18983453"
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_constraint("files_test_id_fkey", "files", type_="foreignkey")
    op.drop_column("files", "test_id")


def downgrade():
    pass
