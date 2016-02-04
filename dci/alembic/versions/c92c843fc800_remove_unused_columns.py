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

"""remove unused columns

Revision ID: c92c843fc800
Revises: 3a7cafffb2e3
Create Date: 2016-01-28 09:08:37.501204

"""

# revision identifiers, used by Alembic.
revision = 'c92c843fc800'
down_revision = '3a7cafffb2e3'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_column('components', 'updated_at')
    op.drop_column('components', 'etag')

    op.drop_column('jobstates', 'updated_at')
    op.drop_column('jobstates', 'etag')

    op.drop_column('files', 'updated_at')
    op.drop_column('files', 'etag')

    op.drop_column('tests', 'updated_at')
    op.drop_column('tests', 'etag')

    constraint = 'jobdefinition_components_component_id_jobdefinition_id_key'
    op.drop_column('jobdefinition_components', 'updated_at')
    op.drop_column('jobdefinition_components', 'created_at')
    op.drop_column('jobdefinition_components', 'etag')
    op.drop_column('jobdefinition_components', 'id')
    op.drop_constraint(constraint, 'jobdefinition_components')
    op.create_primary_key(
        'jobdefinition_components_pkey', 'jobdefinition_components',
        ['component_id', 'jobdefinition_id']
    )

    constraint = 'user_remotecis_user_id_remoteci_id_key'
    op.drop_column('user_remotecis', 'updated_at')
    op.drop_column('user_remotecis', 'created_at')
    op.drop_column('user_remotecis', 'etag')
    op.drop_column('user_remotecis', 'id')
    op.drop_constraint(constraint, 'user_remotecis')
    op.create_primary_key(
        'user_remotecis_pkey', 'user_remotecis', ['user_id', 'remoteci_id']
    )


def downgrade():
    pass
