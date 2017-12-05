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

"""Migrate Metas to Tags

Revision ID: 5758a78a7f58
Revises: 8e1349eb050b
Create Date: 2017-12-05 14:27:12.240840

"""

# revision identifiers, used by Alembic.
revision = '5758a78a7f58'
down_revision = '8e1349eb050b'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.rename_table('metas', 'tags')
    op.drop_index('metas_job_id_idx', 'tags')
    op.create_index('tags_job_id_idx', 'tags', ['job_id'])


def downgrade():
    pass
