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

"""remove_unused_status

Revision ID: 13e98260e36d
Revises: 3ad86da9baab
Create Date: 2018-04-06 20:24:53.843454

"""

# revision identifiers, used by Alembic.
revision = "13e98260e36d"
down_revision = "3ad86da9baab"
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.execute(
        "UPDATE jobs SET status='failure' WHERE status='deployment-failure' or status='product-failure'"
    )
    op.execute(
        "UPDATE jobstates SET status='failure' WHERE status='deployment-failure' or status='product-failure'"
    )
    op.execute("ALTER TYPE statuses RENAME TO statuses_old")
    op.execute(
        "CREATE TYPE statuses AS ENUM('new', 'pre-run', 'running', 'post-run', 'success', 'failure', 'killed')"
    )
    op.execute(
        "ALTER TABLE jobs ALTER COLUMN status TYPE statuses USING status::text::statuses"
    )
    op.execute(
        "ALTER TABLE jobstates ALTER COLUMN status TYPE statuses USING status::text::statuses"
    )
    op.execute("DROP TYPE statuses_old")


def downgrade():
    pass
