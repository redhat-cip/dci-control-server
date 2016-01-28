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

"""unique name against teams

Revision ID: d7be5a166b42
Revises: c92c843fc800
Create Date: 2016-01-28 16:11:56.069002

"""

# revision identifiers, used by Alembic.
revision = 'd7be5a166b42'
down_revision = 'c92c843fc800'
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
