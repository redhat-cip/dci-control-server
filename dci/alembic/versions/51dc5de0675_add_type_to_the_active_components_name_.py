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

"""Add type to the active_components_name_topic_id_key

Revision ID: 51dc5de0675
Revises: 406efd744a11
Create Date: 2019-04-02 18:29:21.409236

"""

# revision identifiers, used by Alembic.
revision = "51dc5de0675"
down_revision = "406efd744a11"
branch_labels = None
depends_on = None

from alembic import op
from sqlalchemy import text


def upgrade():
    op.drop_index(
        index_name="active_components_name_topic_id_key", table_name="components"
    )
    op.create_index(
        index_name="active_components_name_topic_id_key",
        table_name="components",
        columns=["name", "topic_id", "type"],
        unique=True,
        postgresql_where=text("components.state = 'active'"),
    )


def downgrade():
    op.drop_index(
        index_name="active_components_name_topic_id_key", table_name="components"
    )
    op.create_index(
        index_name="active_components_name_topic_id_key",
        table_name="components",
        columns=["name", "topic_id"],
        unique=True,
        postgresql_where=text("components.state = 'active'"),
    )
