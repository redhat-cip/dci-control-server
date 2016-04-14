#
# Copyright (C) 2016 Red Hat, Inc
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

"""Make files content nullable

Revision ID: 9ba5bcab9aef
Revises: 89638be0fc0f
Create Date: 2016-05-08 17:29:39.706742

"""

# revision identifiers, used by Alembic.
revision = '9ba5bcab9aef'
down_revision = '89638be0fc0f'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.alter_column("files", "content", nullable=True)


def downgrade():
    pass
