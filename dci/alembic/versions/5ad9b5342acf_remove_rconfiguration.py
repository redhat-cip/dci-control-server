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

"""Remove rconfiguration

Revision ID: 5ad9b5342acf
Revises: 7a7edb42a22
Create Date: 2019-07-29 10:51:27.152354

"""

# revision identifiers, used by Alembic.
revision = '5ad9b5342acf'
down_revision = '7a7edb42a22'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_index('jobs_rconfiguration_id_idx', table_name='jobs')
    op.drop_constraint(u'jobs_rconfiguration_id_fkey', 'jobs', type_='foreignkey')
    op.drop_column('jobs', 'rconfiguration_id')
    op.drop_table('remotecis_rconfigurations')
    op.drop_table('rconfigurations')


def downgrade():
    pass
