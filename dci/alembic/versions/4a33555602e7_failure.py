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

"""failure

Revision ID: 4a33555602e7
Revises: 5d48174e4f24
Create Date: 2017-08-01 15:42:55.266784

"""

# revision identifiers, used by Alembic.
revision = '4a33555602e7'
down_revision = '5d48174e4f24'
branch_labels = None
depends_on = None

from alembic import op
from sqlalchemy import sql

from dci.db import models


def upgrade():
    db_conn = op.get_bind()
    with db_conn.begin() as conn:
        query = sql.select([models.JOBS])
        conn.execute(query).fetchall()
        raise


def downgrade():
    pass
