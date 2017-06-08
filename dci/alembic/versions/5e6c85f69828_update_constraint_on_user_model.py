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

"""update_constraint_on_user_model

Revision ID: 5e6c85f69828
Revises: 632fccdeea6d
Create Date: 2017-06-15 11:24:35.743678

"""

# revision identifiers, used by Alembic.
revision = '5e6c85f69828'
down_revision = '632fccdeea6d'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('fullname', nullable=False)
        batch_op.alter_column('email', nullable=False)
        batch_op.create_unique_constraint('users_email', ['email'])


def downgrade():
    pass
