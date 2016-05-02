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

"""Add components_hash column to jobs

Revision ID: f8caf73e0901
Revises: e6c96dce3b95
Create Date: 2016-05-02 14:31:11.010112

"""

# revision identifiers, used by Alembic.
revision = 'f8caf73e0901'
down_revision = 'e6c96dce3b95'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('jobs', sa.Column('components_hash',
                                    sa.String(32), nullable=True))


def downgrade():
    pass
