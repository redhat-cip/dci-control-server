#
# Copyright (C) 2022 Red Hat, Inc
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

"""null component_types_optional default value

Revision ID: 24963e101d13
Revises: 31d87ef60971
Create Date: 2022-02-27 01:39:38.421029

"""

# revision identifiers, used by Alembic.
revision = "24963e101d13"
down_revision = "31d87ef60971"
branch_labels = None
depends_on = None

from alembic import op
from sqlalchemy.orm.session import Session
from dci.db import models2


def upgrade():
    session = Session(op.get_bind())

    for topic in (
        session.query(models2.Topic)
        .filter(models2.Topic.component_types_optional == None)  # noqa
        .all()
    ):
        topic.component_types_optional = []

    session.commit()


def downgrade():
    pass
