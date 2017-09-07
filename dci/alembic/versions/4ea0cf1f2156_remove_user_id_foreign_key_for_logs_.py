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

"""remove user id foreign key for logs table

Revision ID: 4ea0cf1f2156
Revises: 6e0426896841
Create Date: 2017-08-02 18:43:44.823612

"""

# revision identifiers, used by Alembic.
revision = '4ea0cf1f2156'
down_revision = '6e0426896841'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_constraint('logs_user_id_fkey', 'logs')


def downgrade():
    pass
