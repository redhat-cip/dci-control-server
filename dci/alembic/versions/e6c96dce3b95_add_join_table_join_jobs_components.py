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
from sqlalchemy.dialects import postgres as pg
from sqlalchemy import sql


_COMPONENTS = sa.Table(
    'components', sa.MetaData(),
    sa.Column('id', sa.String(36), primary_key=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('name', sa.String(255), nullable=False),
    sa.Column('type', sa.String(255), nullable=False),
    sa.Column('canonical_project_name', sa.String),
    sa.Column('sha', sa.Text),
    sa.Column('title', sa.Text),
    sa.Column('message', sa.Text),
    sa.Column('url', sa.Text),
    sa.Column('git', sa.Text),
    sa.Column('ref', sa.Text),
    sa.Column('topic_id', sa.String(36),
              sa.ForeignKey('topics.id', ondelete="CASCADE"),
              nullable=True),
    sa.UniqueConstraint('name', 'topic_id',
                        name='components_name_topic_id_key'))

_JOBDEFINITIONS = sa.Table(
    'jobdefinitions', sa.MetaData(),
    sa.Column('id', sa.String(36), primary_key=True),
    sa.Column('created_at', sa.DateTime()),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('etag', sa.String(40), nullable=False),
    sa.Column('name', sa.String(255)),
    sa.Column('priority', sa.Integer, default=0),
    sa.Column('type', sa.String(255), default=""),
    sa.Column('topic_id', sa.String(36),
              sa.ForeignKey('topics.id', ondelete="CASCADE"),
              nullable=True),
    sa.Column('active', sa.BOOLEAN, default=True),
    sa.Column('comment', sa.Text),
    sa.Column('component_types', pg.JSON, default=[]),
)

_JOBS = sa.Table(
    'jobs', sa.MetaData(),
    sa.Column('id', sa.String(36), primary_key=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('etag', sa.String(40), nullable=False),
    sa.Column('comment', sa.Text),
    sa.Column('recheck', sa.Boolean, default=False),
    sa.Column('configuration', pg.JSON, default={}),
    sa.Column('jobdefinition_id', sa.String(36),
              sa.ForeignKey('jobdefinitions.id', ondelete="CASCADE"),
              nullable=False),
    sa.Column('remoteci_id', sa.String(36),
              sa.ForeignKey('remotecis.id', ondelete="CASCADE"),
              nullable=False),
    sa.Column('team_id', sa.String(36),
              sa.ForeignKey('teams.id', ondelete="CASCADE"),
              nullable=False))

_JOINS_JOBS_COMPONENTS = sa.Table(
    'jobs_components', sa.MetaData(),
    sa.Column('job_id', sa.String(36),
              sa.ForeignKey('jobs.id', ondelete="CASCADE"),
              nullable=False, primary_key=True),
    sa.Column('component_id', sa.String(36),
              sa.ForeignKey('components.id', ondelete="CASCADE"),
              nullable=False, primary_key=True))


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
        sql.select([_JOBDEFINITIONS])).fetchall()
    for jd in all_jobdefinitions:
        component_types = []
        jd = dict(jd)
        jd_id = jd['id']
        all_components = db_conn.execute(
            sql.select([_COMPONENTS])).fetchall()
        all_jobs = db_conn.execute(sql.select([_JOBS])).fetchall()
        for cmpt in all_components:
            cmpt = dict(cmpt)
            component_types.append(cmpt['type'])
            # feed jobs_components table with existing datas
            for job in all_jobs:
                job = dict(job)
                db_conn.execute(
                    _JOINS_JOBS_COMPONENTS.insert().values(
                        job_id=job['id'], component_id=cmpt['id']))
        # update the component type list of the current jobdefinition
        _JOBDEFINITIONS.update().where(
            _JOBDEFINITIONS.c.id == jd_id).values(
            component_types=component_types)

    # feed jobs_components table with existing datas
    all_jobs = db_conn.execute(
        sql.select([_JOBS])).fetchall()
    for job in all_jobs:
        job = dict(job)
        jd_id = job['jobdefinition_id']


def downgrade():
    pass
