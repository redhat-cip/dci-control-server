#
# Copyright (C) 2018 Red Hat, Inc
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

"""Remove remoteci data

Revision ID: f602855825c0
Revises: b71a4139c14f
Create Date: 2018-09-20 18:59:52.106946

"""

# revision identifiers, used by Alembic.
revision = 'f602855825c0'
down_revision = 'b71a4139c14f'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_column('remotecis', 'data')


def downgrade():
    pass
