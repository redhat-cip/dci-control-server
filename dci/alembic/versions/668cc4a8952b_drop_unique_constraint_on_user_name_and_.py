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

"""drop unique constraint on user name and team_id

Revision ID: 668cc4a8952b
Revises: a8af12d3d5aa
Create Date: 2016-03-03 14:59:30.313242

"""

# revision identifiers, used by Alembic.
revision = '668cc4a8952b'
down_revision = 'a8af12d3d5aa'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_constraint('users_name_team_id_key', 'users')
    op.create_unique_constraint('users_name_key', 'users', ['name'])


def downgrade():
    pass
