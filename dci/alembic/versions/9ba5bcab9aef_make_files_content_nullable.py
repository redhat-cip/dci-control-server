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
from dci.db import models
from dci import dci_config


from alembic import op
from sqlalchemy import sql


_FILES_FOLDER = dci_config.generate_conf()['FILES_UPLOAD_FOLDER']


def upgrade():
    op.alter_column("files", "content", nullable=True)
    db_conn = op.get_bind()

    query_count_files = sql.select([sql.func.count(models.FILES.c.id)]).\
        as_scalar()
    nb_files = db_conn.execute(query_count_files)

    query_file = sql.select([models.FILES])
    for index in xrange(0, nb_files):
        file = db_conn.execute(query_file.offset(index).limit(1))
        file = dict(file)

        # ensure the team path exist in the FS
        v1_utils.ensure_path_exists('%s/%s' % (_FILES_FOLDER, file['team_id']))
        file_path = '%s/%s/%s' % (_FILES_FOLDER, file['team_id'], file['id'])

        with open(file_path, "wb") as f:
            f.write(file['content'])


def downgrade():
    pass
