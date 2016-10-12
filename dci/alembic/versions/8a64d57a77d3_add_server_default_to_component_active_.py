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

"""add server_default to component active flag

Revision ID: 8a64d57a77d3
Revises: cc020d3f2290
Create Date: 2016-10-12 11:47:08.609980

"""

# revision identifiers, used by Alembic.
revision = '8a64d57a77d3'
down_revision = 'cc020d3f2290'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.alter_column('components', 'active', server_default=True)


def downgrade():
    pass
