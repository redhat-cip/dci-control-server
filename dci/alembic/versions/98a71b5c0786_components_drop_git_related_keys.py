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

"""components: drop git related keys

Revision ID: 98a71b5c0786
Revises: c6b58b245108
Create Date: 2016-10-03 16:04:14.266278

"""

# revision identifiers, used by Alembic.
revision = '98a71b5c0786'
down_revision = 'c6b58b245108'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_column('components', 'sha')
    op.drop_column('components', 'git')
    op.drop_column('components', 'ref')


def downgrade():
    pass
