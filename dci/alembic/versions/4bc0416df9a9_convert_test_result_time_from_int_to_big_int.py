#
# Copyright (C) 2019 Red Hat, Inc
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

"""Convert test result time from int to bigint

Revision ID: 4bc0416df9a9
Revises: 49363052bd7d
Create Date: 2019-10-24 07:27:34.270983

"""

# revision identifiers, used by Alembic.
revision = '4bc0416df9a9'
down_revision = '49363052bd7d'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('tests_results', 'time', type_=sa.BigInteger)


def downgrade():
    pass
