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

"""add tests_suite column to tests_results

Revision ID: b0436aece81f
Revises: 19dd8a44afdf
Create Date: 2018-01-25 13:08:13.215147

"""

# revision identifiers, used by Alembic.
revision = "b0436aece81f"
down_revision = "19dd8a44afdf"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


def upgrade():
    op.add_column("tests_results", sa.Column("tests_cases", pg.JSON, default=[]))
    op.add_column("tests_results", sa.Column("regressions", sa.Integer, default=0))


def downgrade():
    pass
