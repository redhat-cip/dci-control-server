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

"""drop components export_control

Revision ID: 192940556583
Revises: 296d8a15d478
Create Date: 2019-05-10 14:40:43.042247

"""

# revision identifiers, used by Alembic.
revision = "192940556583"
down_revision = "296d8a15d478"
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_column("components", "export_control")


def downgrade():
    pass
