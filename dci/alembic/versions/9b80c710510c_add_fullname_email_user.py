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

"""add_fullname_email_user

Revision ID: 9b80c710510c
Revises: cba07e5d607d
Create Date: 2017-06-12 09:55:52.136990

"""

# revision identifiers, used by Alembic.
revision = '9b80c710510c'
down_revision = 'cba07e5d607d'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('fullname', sa.String(255)))
        batch_op.add_column(sa.Column('email', sa.String(255)))

    op.execute("UPDATE users SET fullname = name")
    op.execute("UPDATE users SET email = CONCAT(name, '@localhost')")

    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('fullname', nullable=False)
        batch_op.alter_column('email', nullable=False)
        batch_op.create_unique_constraint('users_email', ['email'])


def downgrade():
    pass
