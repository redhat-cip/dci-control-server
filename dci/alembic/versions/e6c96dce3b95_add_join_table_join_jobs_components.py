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
import itertools
import sqlalchemy as sa
from sqlalchemy.dialects import postgres as pg
from sqlalchemy import sql


_COMPONENTS = sa.Table(
    'components', sa.MetaData(),
    sa.Column('id', sa.String(36), primary_key=True),
    sa.Column('type', sa.String(255), nullable=False),
    sa.Column('url', sa.Text))

_JOBDEFINITIONS = sa.Table(
    'jobdefinitions', sa.MetaData(),
    sa.Column('id', sa.String(36), primary_key=True),
    sa.Column('component_types', pg.JSON, default=[]),
)

_JOBS = sa.Table(
    'jobs', sa.MetaData(),
    sa.Column('id', sa.String(36), primary_key=True),
    sa.Column('jobdefinition_id', sa.String(36),
              sa.ForeignKey('jobdefinitions.id', ondelete='CASCADE'),
              nullable=False))

_JOIN_JOBS_COMPONENTS = sa.Table(
    'jobs_components', sa.MetaData(),
    sa.Column('job_id', sa.String(36),
              sa.ForeignKey('jobs.id', ondelete='CASCADE'),
              nullable=False, primary_key=True),
    sa.Column('component_id', sa.String(36),
              sa.ForeignKey('components.id', ondelete='CASCADE'),
              nullable=False, primary_key=True))


def upgrade():
    op.create_table(
        'jobs_components',
        sa.Column('job_id', sa.String(36),
                  sa.ForeignKey('jobs.id', ondelete='CASCADE'),
                  nullable=False, primary_key=True),
        sa.Column('component_id', sa.String(36),
                  sa.ForeignKey('components.id', ondelete='CASCADE'),
                  nullable=False, primary_key=True)
    )

    db_conn = op.get_bind()

    # First update the components type and then update the jobdefinition's
    # components type list.

    # puddle -> puddle_ospd
    update_to_puddle_ospd = (
        _COMPONENTS.update()
        .where(sql.and_(_COMPONENTS.c.url.contains('director'),
                        _COMPONENTS.c.type == 'puddle'))
        .values(type='puddle_ospd')
    )
    db_conn.execute(update_to_puddle_ospd)

    # puddle -> puddle_osp
    update_to_puddle_osp = (
        _COMPONENTS.update()
        .where(sql.and_(sql.not_(_COMPONENTS.c.url.contains('director')),
                        _COMPONENTS.c.type == 'puddle'))
        .values(type='puddle_osp')
    )
    db_conn.execute(update_to_puddle_osp)

    # update jobdefinition's component type list and feed jobs_components
    all_jobdefinitions = (
        db_conn.execute(sql.select([_JOBDEFINITIONS]))
        .fetchall()
    )

    for jd in all_jobdefinitions:
        all_components = db_conn.execute(sql.select([_COMPONENTS])).fetchall()
        all_jobs = db_conn.execute(sql.select([_JOBS])).fetchall()

        component_types = [cmpt['type'] for cmpt in all_components]

        for cmpt, job in itertools.product(all_components, all_jobs):
            query = (_JOIN_JOBS_COMPONENTS
                     .insert()
                     .values(job_id=job['id'], component_id=cmpt['id']))
            db_conn.execute(query)

        # update the component type list of the current jobdefinition
        (_JOBDEFINITIONS
            .update()
            .where(_JOBDEFINITIONS.c.id == jd['id'])
            .values(component_types=component_types))


def downgrade():
    pass
