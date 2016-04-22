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

"""Add join table join_jobs_components

Revision ID: e6c96dce3b95
Revises: 18327b41e11d
Create Date: 2016-04-22 11:12:31.786483

"""

# revision identifiers, used by Alembic.
revision = 'e6c96dce3b95'
down_revision = '18327b41e11d'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy import sql

from dci.db import models


def upgrade():
    op.create_table(
        'jobs_components',
        sa.Column('job_id', sa.String(36),
                  sa.ForeignKey('jobs.id', ondelete="CASCADE"),
                  nullable=False, primary_key=True),
        sa.Column('component_id', sa.String(36),
                  sa.ForeignKey('components.id', ondelete="CASCADE"),
                  nullable=False, primary_key=True)
    )

    db_conn = op.get_bind()

    _COMPONENTS = models.COMPONENTS

    # First update the components type and then update the jobdefinition's
    # components type list.

    # puddle -> puddle_ospd
    update_to_puddle_ospd = _COMPONENTS.update().where(
        sql.and_(_COMPONENTS.c.url.contains('director'),
                 _COMPONENTS.c.type == 'puddle')).values(
        type='puddle_ospd')
    db_conn.execute(update_to_puddle_ospd)

    # puddle -> puddle_osp
    update_to_puddle_osp = _COMPONENTS.update().where(
        sql.and_(sql.not_(_COMPONENTS.c.url.contains('director')),
                 _COMPONENTS.c.type == 'puddle')).values(
        type='puddle_osp')
    db_conn.execute(update_to_puddle_osp)

    # update jobdefinition's component type list and feed jobs_components
    all_jobdefinitions = db_conn.execute(
        sql.select([models.JOBDEFINITIONS])).fetchall()
    for jd in all_jobdefinitions:
        component_types = []
        jd = dict(jd)
        jd_id = jd['id']
        all_components = db_conn.execute(
            sql.select([_COMPONENTS])).fetchall()
        all_jobs = db_conn.execute(sql.select([models.JOBS])).fetchall()
        for cmpt in all_components:
            cmpt = dict(cmpt)
            component_types.append(cmpt['type'])
            # feed jobs_components table with existing datas
            for job in all_jobs:
                job = dict(job)
                db_conn.execute(
                    models.JOINS_JOBS_COMPONENTS.insert().values(
                        job_id=job['id'], component_id=cmpt['id']))
        # update the component type list of the current jobdefinition
        models.JOBDEFINITIONS.update().where(
            models.JOBDEFINITIONS.c.id == jd_id).values(
            component_types=component_types)

    # feed jobs_components table with existing datas
    all_jobs = db_conn.execute(
        sql.select([models.JOBS])).fetchall()
    for job in all_jobs:
        job = dict(job)
        jd_id = job['jobdefinition_id']


def downgrade():
    pass
