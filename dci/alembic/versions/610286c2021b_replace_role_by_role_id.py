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

Revision ID: 610286c2021b
Revises: 4a7aebcd0c28
Create Date: 2017-04-25 13:45:35.981620

"""

# revision identifiers, used by Alembic.
revision = '610286c2021b'
down_revision = '4a7aebcd0c28'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


def upgrade():

    op.drop_column('users', 'role')
    op.add_column('users', sa.Column('role_id', pg.UUID(as_uuid=True),
                  sa.ForeignKey('roles.id', ondelete='SET NULL')))


def downgrade():
    pass
