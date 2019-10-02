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

"""remove user team_id field

Revision ID: dceacd04b09
Revises: 49363052bd7d
Create Date: 2019-10-02 14:45:30.499656

"""

# revision identifiers, used by Alembic.
revision = 'dceacd04b09'
down_revision = '49363052bd7d'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_index('users_team_id_idx', table_name='users')
    op.drop_column('users', 'team_id')


def downgrade():
    pass
