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

"""Add osp-failure deployment-failure and integration statuses

Revision ID: 48c9af8ba5c3
Revises: 348ba02aff54
Create Date: 2016-07-27 10:23:09.962962

"""

# revision identifiers, used by Alembic.
revision = '48c9af8ba5c3'
down_revision = '348ba02aff54'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute('ALTER TYPE statuses RENAME TO statuses_old')
    statuses = sa.Enum('new', 'pre-run', 'running', 'post-run', 'success',
                       'failure', 'killed', 'osp-failure',
                       'deployment-failure', 'integration', name='statuses')
    statuses.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE jobs ALTER COLUMN status TYPE statuses '
               'USING status::text::statuses')
    op.execute('ALTER TABLE jobstates ALTER COLUMN status TYPE statuses '
               'USING status::text::statuses')
    op.execute('DROP TYPE statuses_old')


def downgrade():
    pass
