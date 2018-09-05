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

"""reset etag for users and remotecis

Revision ID: 1cd0d3338c09
Revises: bcd903a35145
Create Date: 2018-09-05 11:37:14.271468

"""

# revision identifiers, used by Alembic.
revision = '1cd0d3338c09'
down_revision = 'bcd903a35145'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
import datetime
import hashlib
import six
import uuid
from sqlalchemy.dialects import postgresql as pg


REMOTECIS = sa.Table(
    'remotecis',
    sa.MetaData(),
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40)),
)


def gen_etag():
    my_salt = str(uuid.uuid4())
    if six.PY2:
        my_salt = my_salt.decode('utf-8')
    elif six.PY3:
        my_salt = my_salt.encode('utf-8')
    md5 = hashlib.md5()
    md5.update(my_salt)
    return md5.hexdigest()


def upgrade():
    db_conn = op.get_bind()
    for row in db_conn.execute(REMOTECIS.select()):
        print(row)
        query = REMOTECIS.update().where(
            REMOTECIS.c.id == row['id']).values(
                {'etag': gen_etag()})
        db_conn.execute(query)


def downgrade():
    pass
