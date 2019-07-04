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

"""remove role

Revision ID: 3eccf653cd30
Revises: 51dc5de0675
Create Date: 2019-04-01 18:42:29.715157

"""

# revision identifiers, used by Alembic.
revision = '3eccf653cd30'
down_revision = '51dc5de0675'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_column('users', 'role_id')
    op.drop_column('remotecis', 'role_id')
    op.drop_table('roles')


def downgrade():
    pass