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

"""unique_name_against_teams

Revision ID: 099abdadf83a
Revises: 41331626e0c0
Create Date: 2016-02-25 11:00:06.163828

"""

# revision identifiers, used by Alembic.
revision = '099abdadf83a'
down_revision = '41331626e0c0'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_constraint('remotecis_name_key', 'remotecis')
    op.drop_constraint('users_name_key', 'users')

    op.create_unique_constraint('remotecis_name_team_id_key', 'remotecis',
                                ['name', 'team_id'])
    op.create_unique_constraint('users_name_team_id_key', 'users',
                                ['name', 'team_id'])


def downgrade():
    pass
