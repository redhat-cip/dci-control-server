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

"""remove_role_team_id

Revision ID: 4d23e0485b37
Revises: 929badc53a9b
Create Date: 2017-05-30 13:37:57.244669

"""

# revision identifiers, used by Alembic.
revision = '4d23e0485b37'
down_revision = '929badc53a9b'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_column('roles', 'team_id')


def downgrade():
    pass
