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

"""RemovePermissions

Revision ID: b71a4139c14f
Revises: 46fa9eb61235
Create Date: 2018-09-19 13:07:20.467918

"""

# revision identifiers, used by Alembic.
revision = "b71a4139c14f"
down_revision = "46fa9eb61235"
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_table("roles_permissions")
    op.drop_table("permissions")


def downgrade():
    pass
