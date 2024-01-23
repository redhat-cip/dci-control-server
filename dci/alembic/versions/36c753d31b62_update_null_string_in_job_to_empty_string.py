#
# Copyright (C) 2024 Red Hat, Inc
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

"""Update null string in job to empty string

Revision ID: 36c753d31b62
Revises: 892f7e0ba88d
Create Date: 2024-01-23 10:33:31.144006

"""

# revision identifiers, used by Alembic.
revision = "36c753d31b62"
down_revision = "892f7e0ba88d"
branch_labels = None
depends_on = None

from alembic import op
from sqlalchemy.orm.session import Session
from sqlalchemy import exc
import sys


def upgrade():
    session = Session(op.get_bind())
    try:
        session.execute("UPDATE jobs SET comment = '' WHERE comment IS NULL")
        session.execute(
            "UPDATE jobs SET status_reason = '' WHERE status_reason IS NULL"
        )
        session.execute(
            "UPDATE jobs SET configuration = '' WHERE configuration IS NULL"
        )
        session.execute("UPDATE jobs SET url = '' WHERE url IS NULL")
        session.execute("UPDATE jobs SET name = '' WHERE name IS NULL")
        session.execute("UPDATE jobs SET user_agent = '' WHERE user_agent IS NULL")
        session.execute(
            "UPDATE jobs SET client_version = '' WHERE client_version IS NULL"
        )
    except exc.IntegrityError as ie:
        print("Rollback " + str(ie))
        session.rollback()
        session.close()
        sys.exit(1)
    except Exception as e:
        print("Exception " + str(e))
        session.rollback()
        session.close()
        sys.exit(1)
    session.commit()
    session.close()


def downgrade():
    pass
