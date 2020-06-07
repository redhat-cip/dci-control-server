#
# Copyright (C) 2020 Red Hat, Inc
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

"""remove user teamid

Revision ID: bad424e096
Revises: 1f29092c3fe
Create Date: 2020-06-07 23:27:19.926911

"""

# revision identifiers, used by Alembic.
revision = 'bad424e096'
down_revision = '1f29092c3fe'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_index('users_team_id_idx', table_name='users')
    op.drop_column('users', 'team_id')


def downgrade():
    pass
