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

"""Add keys column in remoteci

Revision ID: 6647e6ca3982
Revises: 3750c0221184
Create Date: 2018-03-06 11:55:42.870215

"""

# revision identifiers, used by Alembic.
revision = "6647e6ca3982"
down_revision = "3750c0221184"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("remotecis", sa.Column("cert_fp", sa.String(255)))


def downgrade():
    pass
