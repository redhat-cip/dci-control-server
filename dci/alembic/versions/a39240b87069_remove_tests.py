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

"""remove tests

Revision ID: a39240b87069
Revises: 60da2e535edb
Create Date: 2022-03-10 04:47:44.141573

"""

# revision identifiers, used by Alembic.
revision = "a39240b87069"
down_revision = "60da2e535edb"
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_table("tests")


def downgrade():
    pass
