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

"""add_product_id_to_topic

Revision ID: f381f939cd0b
Revises: d57891964026
Create Date: 2017-08-08 08:38:31.487898

"""

# revision identifiers, used by Alembic.
revision = 'f381f939cd0b'
down_revision = 'd57891964026'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


def upgrade():
    op.add_column('topics', sa.Column('product_id', pg.UUID(as_uuid=True),
                                      sa.ForeignKey('products.id'),
                                      nullable=True))
    op.create_index('topics_product_id_idx', 'topics', ['product_id'])


def downgrade():
    pass
