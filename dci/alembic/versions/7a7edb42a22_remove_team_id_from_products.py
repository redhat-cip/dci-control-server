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

"""remove team_id from products

Revision ID: 7a7edb42a22
Revises: 2c7bc5614cf8
Create Date: 2019-07-04 17:43:16.355388

"""

# revision identifiers, used by Alembic.
revision = '7a7edb42a22'
down_revision = '2c7bc5614cf8'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_column('products', 'team_id')


def downgrade():
    pass
