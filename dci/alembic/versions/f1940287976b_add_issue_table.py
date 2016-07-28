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

"""Add issue table

Revision ID: f1940287976b
Revises: 48c9af8ba5c3
Create Date: 2016-07-29 09:22:49.606519

"""

# revision identifiers, used by Alembic.
revision = 'f1940287976b'
down_revision = '48c9af8ba5c3'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    trackers = sa.Enum('github', 'bugzilla', name='trackers')

    op.create_table(
        'issues',
        sa.Column('id', sa.String(36), primary_key=True,
                  default=utils.gen_uuid),
        sa.Column('created_at', sa.DateTime(),
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('updated_at', sa.DateTime(),
                  onupdate=datetime.datetime.utcnow,
                  default=datetime.datetime.utcnow, nullable=False),
        sa.Column('url', sa.Text, unique=True),
        sa.Column('tracker', trackers, nullable=False)
    )

    op.create_table(
        'jobs_issues',
        sa.Column('job_id', sa.String(36),
                  sa.ForeignKey('jobs.id', ondelete="CASCADE"),
                  nullable=False, primary_key=True),
        sa.Column('issue_id', sa.String(36),
                  sa.ForeignKey('issues.id', ondelete="CASCADE"),
                  nullable=False, primary_key=True)
    )


def downgrade():
    pass
