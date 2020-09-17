#
# Copyright (C) 2018 Red Hat, Inc
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

"""constaint_component_unique_name

Revision ID: b4a4e3568d82
Revises: 3cdd5a268c45
Create Date: 2018-05-14 21:26:26.082607

"""

# revision identifiers, used by Alembic.
revision = "b4a4e3568d82"
down_revision = "eba69907de79"
branch_labels = None
depends_on = None

from alembic import op
from sqlalchemy.sql import text


def upgrade():
    op.create_index(
        index_name="active_components_name_topic_id_key",
        table_name="components",
        columns=["name", "topic_id"],
        unique=True,
        postgresql_where=text("components.state = 'active'"),
    )
    op.drop_constraint(
        constraint_name="components_name_topic_id_key", table_name="components"
    )


def downgrade():
    op.create_unique_constraint(
        name="components_name_topic_id_key",
        table_name="components",
        columns=["name", "topic_id"],
    )
    op.drop_index(
        index_name="active_components_name_topic_id_key", table_name="components"
    )
