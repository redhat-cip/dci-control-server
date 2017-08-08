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

import datetime
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
import dci.common.utils as utils

RESOURCE_STATES = ['active', 'inactive', 'archived']
STATES = sa.Enum(*RESOURCE_STATES, name='states')

PRODUCTS = sa.Table(
    'products', sa.MetaData(),
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
    sa.Column('name', sa.String(255), nullable=False),
    sa.Column('label', sa.String(255), nullable=False, unique=True),
    sa.Column('description', sa.Text),
    sa.Column('state', STATES, default='active')
)


def upgrade():

    db_conn = op.get_bind()

    product_id = utils.gen_uuid()
    product_values = {
        'id': product_id,
        'created_at': datetime.datetime.utcnow().isoformat(),
        'updated_at': datetime.datetime.utcnow().isoformat(),
        'etag': utils.gen_etag(),
        'name': 'Genesis',
        'label': 'GENESIS',
        'description': 'The Genesis Product'
    }
    db_conn.execute(PRODUCTS.insert().values(**product_values))

    op.add_column('topics', sa.Column('product_id', pg.UUID(as_uuid=True),
                                      sa.ForeignKey('products.id'),
                                      nullable=False,
                                      server_default=product_id))


def downgrade():
    pass
