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

"""remove_priority_field

Revision ID: 89b22c9a9a70
Revises: 4d23e0485b37
Create Date: 2017-05-31 12:06:43.956668

"""

# revision identifiers, used by Alembic.
revision = '89b22c9a9a70'
down_revision = '4d23e0485b37'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_column('jobdefinitions', 'priority')


def downgrade():
    pass
