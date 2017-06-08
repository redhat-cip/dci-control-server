#
# Copyright (C) 2017 Red Hat, Inc
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

"""remove_user_role_column

Revision ID: cba07e5d607d
Revises: 64c7711477db
Create Date: 2017-06-08 13:57:10.656395

"""

# revision identifiers, used by Alembic.
revision = 'cba07e5d607d'
down_revision = '64c7711477db'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_column('users', 'role')


def downgrade():
    pass
