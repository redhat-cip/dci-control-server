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

"""change role and status from varchar to enums

Revision ID: 3a7cafffb2e3
Revises: 07630dc60809
Create Date: 2016-01-26 11:00:05.977551

"""

# revision identifiers, used by Alembic.
revision = '3a7cafffb2e3'
down_revision = '07630dc60809'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    roles = sa.Enum('user', 'admin', name='roles')
    roles.create(op.get_bind(), checkfirst=False)
    op.execute(
        'ALTER TABLE users ALTER COLUMN role TYPE roles USING role::roles'
    )

    statuses = sa.Enum('new', 'pre-run', 'running', 'post-run', 'success',
                       'failure', name='statuses')
    statuses.create(op.get_bind(), checkfirst=False)

    op.execute('ALTER TABLE jobs ALTER COLUMN status TYPE statuses '
               'USING status::statuses')

    op.execute('ALTER TABLE jobstates ALTER COLUMN status TYPE statuses '
               'USING status::statuses')


def downgrade():
    """Not supported at this time, will be implemented later"""
