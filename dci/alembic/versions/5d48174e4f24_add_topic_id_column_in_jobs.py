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

"""Add topic_id column in jobs

Revision ID: 5d48174e4f24
Revises: af7a9b76939b
Create Date: 2017-07-08 16:15:17.929962

"""

# revision identifiers, used by Alembic.
revision = '5d48174e4f24'
down_revision = 'af7a9b76939b'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

import datetime
from dci.common import utils


JOBDEFINITIONS = sa.Table(
    'jobdefinitions', sa.MetaData(),
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
              default=utils.gen_uuid),
    sa.Column('created_at', sa.DateTime(),
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('updated_at', sa.DateTime(),
              onupdate=datetime.datetime.utcnow,
              default=datetime.datetime.utcnow, nullable=False),
    sa.Column('etag', sa.String(40), nullable=False, default=utils.gen_etag,
              onupdate=utils.gen_etag),
    sa.Column('name', sa.String(255)),
    sa.Column('topic_id', pg.UUID(as_uuid=True),
              sa.ForeignKey('topics.id', ondelete='CASCADE'),
              nullable=True),
    sa.Index('jobdefinitions_topic_id_idx', 'topic_id'),
    sa.Column('comment', sa.Text),
    sa.Column('component_types', pg.JSON, default=[]),
)


def upgrade():

    db_conn = op.get_bind()
    with db_conn.begin():
        op.add_column('jobs',
                      sa.Column('topic_id', pg.UUID(as_uuid=True),
                                sa.ForeignKey('topics.id', ondelete='CASCADE'),
                                # Will be False when jobdefinition will be
                                # removed
                                nullable=True))
        op.create_index('jobs_topic_id_idx', 'jobs', ['topic_id'])


def downgrade():
    pass
