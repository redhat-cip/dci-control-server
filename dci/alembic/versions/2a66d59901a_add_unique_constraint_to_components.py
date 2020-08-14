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

"""add_unique_constraint_to_components

Revision ID: 2a66d59901a
Revises: c5bbe7b63a
Create Date: 2020-08-19 17:28:27.973246

"""

# revision identifiers, used by Alembic.
revision = '2a66d59901a'
down_revision = 'c5bbe7b63a'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_index(index_name='active_components_name_topic_id_team_id_null_key',
                    table_name='components',
                    columns=['name', 'topic_id', 'type'],
                    unique=True,
                    postgresql_where=sa.sql.text("components.state = 'active' AND components.team_id is NULL"))

    op.create_unique_constraint('name_topic_id_type_team_id_unique', 'components', ['name', 'topic_id', 'type', 'team_id'])


def downgrade():
    pass
