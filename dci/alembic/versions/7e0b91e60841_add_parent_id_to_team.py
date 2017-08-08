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

"""add_parent_id_to_team

Revision ID: 7e0b91e60841
Revises: 49b66daed760
Create Date: 2017-08-08 14:24:07.005978

"""

# revision identifiers, used by Alembic.
revision = '7e0b91e60841'
down_revision = '49b66daed760'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


def upgrade():
    op.add_column('teams', sa.Column('parent_id', pg.UUID(as_uuid=True),
                                     sa.ForeignKey('teams.id',
                                                   ondelete='SET NULL'),
                                     nullable=True))


def downgrade():
    pass
