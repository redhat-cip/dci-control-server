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

"""Create files events on existing datas

Revision ID: ad1134e557de
Revises: 61b68c2d66b5
Create Date: 2017-04-21 15:20:00.263439

"""

# revision identifiers, used by Alembic.
revision = 'ad1134e557de'
down_revision = '61b68c2d66b5'
branch_labels = None
depends_on = None

from dci.db import models

from alembic import op
from sqlalchemy.dialects import postgresql as pg
import sqlalchemy as sa
from sqlalchemy import sql


FILES = sa.Table(
    'files', sa.MetaData(),
    sa.Column('id', pg.UUID(as_uuid=True), primary_key=True))


def upgrade():
    db_conn = op.get_bind()

    query_all_files_ids = sql.select([FILES.c.id])
    all_files_ids = db_conn.execute(query_all_files_ids).fetchall()

    for file_id in all_files_ids:
        values = {'file_id': file_id,
                  'action': models.FILES_CREATE}
        q_add_file_event = models.FILES_EVENTS.insert().values(**values)
        db_conn.execute(q_add_file_event)


def downgrade():
    pass
