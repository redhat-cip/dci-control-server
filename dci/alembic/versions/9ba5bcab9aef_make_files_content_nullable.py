#
# Copyright (C) 2016 Red Hat, Inc
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

"""Make files content nullable

Revision ID: 9ba5bcab9aef
Revises: 89638be0fc0f
Create Date: 2016-05-08 17:29:39.706742

"""

# revision identifiers, used by Alembic.
revision = '9ba5bcab9aef'
down_revision = '89638be0fc0f'
branch_labels = None
depends_on = None

from dci.api.v1 import utils as v1_utils
from dci import dci_config

from alembic import op
import sqlalchemy as sa
from sqlalchemy import sql


_FILES_FOLDER = dci_config.generate_conf()['FILES_UPLOAD_FOLDER']
FILES = sa.Table(
    'files', sa.MetaData(),
    sa.Column('id', sa.String(36)),
    sa.Column('content', sa.Text),
    sa.Column('team_id', sa.String(36)))


# move the file's content from the database to the filesystem
def upgrade():
    db_conn = op.get_bind()

    # iterate over the files one by one so that to not explode the memory
    # count the number of files and then iterate
    query_count_files = sql.select([sql.func.count(FILES.c.id)])
    nb_files = db_conn.execute(query_count_files).scalar()

    query_file = sql.select([FILES])
    for index in range(0, nb_files):
        file = db_conn.execute(query_file.offset(index).limit(1)).fetchone()
        file = dict(file)

        file_path = v1_utils.build_file_path(
            _FILES_FOLDER, file['team_id'], file['id']
        )
        with open(file_path, 'w') as f:
            f.write(file['content'])

    # make the file's content nullable
    op.alter_column('files', 'content', nullable=True)


def downgrade():
    pass
