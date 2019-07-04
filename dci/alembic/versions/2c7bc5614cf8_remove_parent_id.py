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

"""remove parent id

Revision ID: 2c7bc5614cf8
Revises: 192940556583
Create Date: 2019-07-04 14:37:10.090406

"""

# revision identifiers, used by Alembic.
revision = '2c7bc5614cf8'
down_revision = 'a46098d949c'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_constraint(constraint_name='teams_name_parent_id_key',
                       table_name='teams')
    op.drop_column('teams', 'parent_id')
    op.create_unique_constraint(name='teams_name_key',
                                table_name='teams',
                                columns=['name']
                                )


def downgrade():
    pass
