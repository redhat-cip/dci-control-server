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

"""Delete old unused notification system

Revision ID: 6e0426896841
Revises: 7e0b91e60841
Create Date: 2017-07-25 16:02:07.706259

"""

# revision identifiers, used by Alembic.
revision = '6e0426896841'
down_revision = '7e0b91e60841'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_column('teams', 'email')
    op.drop_column('teams', 'notification')


def downgrade():
    pass
