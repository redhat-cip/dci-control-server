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

"""Add unique constraint to components name and topic_id

Revision ID: a8af12d3d5aa
Revises: e4d599796fd4
Create Date: 2016-03-02 14:32:19.054896

"""

# revision identifiers, used by Alembic.
revision = 'a8af12d3d5aa'
down_revision = 'e4d599796fd4'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_constraint('components_name_key', 'components')

    op.create_unique_constraint('components_name_topic_id_key', 'components',
                                ['name', 'topic_id'])


def downgrade():
    pass
