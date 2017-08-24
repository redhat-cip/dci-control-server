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

"""add_product_owner_role

Revision ID: 992bd9b61eec
Revises: 7e0b91e60841
Create Date: 2017-08-24 09:58:15.956963

"""

# revision identifiers, used by Alembic.
revision = '992bd9b61eec'
down_revision = '7e0b91e60841'
branch_labels = None
depends_on = None

import datetime
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
import dci.common.utils as utils

RESOURCE_STATES = ['active', 'inactive', 'archived']
STATES = sa.Enum(*RESOURCE_STATES, name='states')

ROLES = sa.Table(
    'roles', sa.MetaData(),
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
    sa.Column('label', sa.String(255), nullable=False),
    sa.Column('description', sa.Text),
    sa.UniqueConstraint('label', name='roles_label_key'),
    sa.Column('state', STATES, default='active')
)


def upgrade():
    db_conn = op.get_bind()
    product_owner_id = utils.gen_uuid()
    product_owner_role = {
        'id': product_owner_id,
        'created_at': datetime.datetime.utcnow().isoformat(),
        'updated_at': datetime.datetime.utcnow().isoformat(),
        'etag': utils.gen_etag(),
        'name': 'Product Owner',
        'label': 'PRODUCT_OWNER',
        'description': 'Product Owner',
    }
    db_conn.execute(ROLES.insert().values(**product_owner_role))


def downgrade():
    pass
