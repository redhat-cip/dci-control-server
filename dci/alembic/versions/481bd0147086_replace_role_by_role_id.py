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

"""replace_role_by_role_id

Revision ID: 481bd0147086
Revises: c39fa4b03edf
Create Date: 2017-05-11 12:52:32.314309

"""

# revision identifiers, used by Alembic.
revision = '481bd0147086'
down_revision = 'c39fa4b03edf'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


def upgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('role_id',
                                      pg.UUID(as_uuid=True),
                                      sa.ForeignKey('roles.id',
                                                    ondelete='SET NULL')))
        batch_op.drop_column('role')


def downgrade():
    pass
