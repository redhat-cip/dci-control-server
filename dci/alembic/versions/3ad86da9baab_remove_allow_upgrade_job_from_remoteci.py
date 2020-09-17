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

"""remove_allow_upgrade_job_from_remoteci

Revision ID: 3ad86da9baab
Revises: 492d4ca8c7df
Create Date: 2018-04-05 15:02:04.432587

"""

# revision identifiers, used by Alembic.
revision = "3ad86da9baab"
down_revision = "492d4ca8c7df"
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_column("remotecis", "allow_upgrade_job")


def downgrade():
    pass
