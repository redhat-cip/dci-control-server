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

"""drop jobdefinitions.type

Revision ID: 418030c694de
Revises: e6c96dce3b95
Create Date: 2016-06-16 10:38:37.868130

"""

# revision identifiers, used by Alembic.
revision = '418030c694de'
down_revision = 'e6c96dce3b95'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_column('jobdefinitions', 'type')


def downgrade():
    pass
