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

"""Remove content column from files

Revision ID: 1a8effae3deb
Revises: 463d8023ce19
Create Date: 2016-04-14 16:00:20.100660

"""

# revision identifiers, used by Alembic.
revision = '1a8effae3deb'
down_revision = '463d8023ce19'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('files', 'content')


def downgrade():
    pass
