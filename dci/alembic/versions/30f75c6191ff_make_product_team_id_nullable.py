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

"""make product team_id nullable

Revision ID: 30f75c6191ff
Revises: a46098d949c
Create Date: 2019-07-15 12:45:39.125473

"""

# revision identifiers, used by Alembic.
revision = "30f75c6191ff"
down_revision = "a46098d949c"
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.alter_column("products", "team_id", nullable=True)


def downgrade():
    pass
