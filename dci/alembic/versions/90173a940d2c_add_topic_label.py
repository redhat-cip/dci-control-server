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

"""add topic.comment

Revision ID: 90173a940d2c
Revises: f1940287976b
Create Date: 2016-08-12 17:53:52.921470

"""

# revision identifiers, used by Alembic.
revision = '90173a940d2c'
down_revision = 'f1940287976b'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('topics', sa.Column('label', sa.Text))


def downgrade():
    pass
