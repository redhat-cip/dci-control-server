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

"""make nonable rconfiguration component types

Revision ID: 8e1349eb050b
Revises: 446d2220f8ea
Create Date: 2017-10-27 00:44:56.315444

"""

# revision identifiers, used by Alembic.
revision = "8e1349eb050b"
down_revision = "446d2220f8ea"
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.alter_column("rconfigurations", "component_types", nullable=True)


def downgrade():
    pass
