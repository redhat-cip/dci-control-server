#
# Copyright (C) 2017 Red Hat, Inc
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

"""Change varchar ID to UUID

Revision ID: 1bb42ff54435
Revises: 75a91edc23b8
Create Date: 2017-02-07 09:28:37.493302

"""

# revision identifiers, used by Alembic.
revision = '1bb42ff54435'
down_revision = '75a91edc23b8'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


def upgrade():
    # Components
    # Drop constraint
    op.drop_constraint('component_files_component_id_fkey', 'component_files')
    op.drop_constraint('jobs_components_component_id_fkey', 'jobs_components')

    # Change type
    op.execute("ALTER TABLE component_files ALTER COLUMN component_id TYPE \
               UUID USING component_id::uuid")
    op.execute("ALTER TABLE jobs_components ALTER COLUMN component_id TYPE \
               UUID USING component_id::uuid")
    op.execute("ALTER TABLE components ALTER COLUMN id TYPE \
               UUID USING id::uuid")
    # Use this when we pass to alembic 0.8.8
    # op.alter_column('component_files', 'component_id', type_=UUID(),
    #                 postgresql_using="component_id::uuid")
    # op.alter_column('jobs_components', 'component_id', type_=UUID(),
    #                 postgresql_using="component_id::uuid")
    # op.alter_column('components', 'id', type_=UUID(),
    #                 postgresql_using="id::uuid")

    # Create constraint
    op.create_foreign_key('component_files_component_id_fkey',
                          'component_files', 'components',
                          ['component_id'], ['id'])
    op.create_foreign_key('jobs_components_component_id_fkey',
                          'jobs_components', 'components',
                          ['component_id'], ['id'])


def downgrade():
    pass
