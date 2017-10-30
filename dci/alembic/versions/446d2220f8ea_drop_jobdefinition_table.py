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

"""drop jobdefinition table

Revision ID: 446d2220f8ea
Revises: 827c558895bc
Create Date: 2017-10-30 15:03:42.307160

"""

# revision identifiers, used by Alembic.
revision = '446d2220f8ea'
down_revision = '827c558895bc'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_index('jobs', 'jobs_jobdefinition_id_idx')
    op.drop_column('jobs', 'jobdefinition_id')
    op.drop_table('jobdefinition_tests')
    op.drop_table('jobdefinition')


def downgrade():
    pass
