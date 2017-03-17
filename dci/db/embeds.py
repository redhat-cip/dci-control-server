# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Red Hat, Inc
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

from dci.db import models

from sqlalchemy import sql
from sqlalchemy.sql import and_


def ignore_columns_from_table(table, ignored_columns):
    return [getattr(table.c, column.name)
            for column in table.columns
            if column.name not in ignored_columns]

# These functions should be called by v1_utils.QueryBuilder

# Create necessary aliases
REMOTECI_TESTS = models.TESTS.alias('remoteci.tests')
JOBDEFINITION_TESTS = models.TESTS.alias('jobdefinition.tests')
TEAM = models.TEAMS.alias('team')
REMOTECI = models.REMOTECIS.alias('remoteci')
CFILES = models.COMPONENT_FILES.alias('files')

JOB = models.JOBS.alias('job')
JOB_WITHOUT_CONFIGURATION = ignore_columns_from_table(JOB, ['configuration'])  # noqa
JOBS_WITHOUT_CONFIGURATION = ignore_columns_from_table(models.JOBS, ['configuration'])  # noqa

LASTJOB = models.JOBS.alias('lastjob')
LASTJOB_WITHOUT_CONFIGURATION = ignore_columns_from_table(LASTJOB, ['configuration'])  # noqa
LASTJOB_COMPONENTS = models.COMPONENTS.alias('lastjob.components')
LASTJOB_JOIN_COMPONENTS = models.JOIN_JOBS_COMPONENTS.alias('lastjob.jobcomponents')  # noqa

CURRENTJOB = models.JOBS.alias('currentjob')
CURRENTJOB_WITHOUT_CONFIGURATION = ignore_columns_from_table(CURRENTJOB, ['configuration'])  # noqa
CURRENTJOB_COMPONENTS = models.COMPONENTS.alias('currentjob.components')
CURRENTJOB_JOIN_COMPONENTS = models.JOIN_JOBS_COMPONENTS.alias('currentjob.jobcomponents')  # noqa

JOBSTATE = models.JOBSTATES.alias('jobstate')
JOBSTATE_JOBS = models.JOBS.alias('jobstate.job')
JOBSTATEJOBS_WITHOUT_CONFIGURATION = ignore_columns_from_table(JOBSTATE_JOBS, ['configuration'])  # noqa


def jobs(root_select=models.JOBS):
    return {
        'files': [
            {'right': models.FILES,
             'onclause': and_(models.FILES.c.job_id == root_select.c.id,
                              models.FILES.c.state != 'archived'),
             'isouter': True}],
        'metas': [
            {'right': models.METAS,
             'onclause': models.METAS.c.job_id == root_select.c.id,
             'isouter': True}],
        'jobdefinition': [
            {'right': models.JOBDEFINITIONS,
             'onclause': and_(root_select.c.jobdefinition_id == models.JOBDEFINITIONS.c.id,  # noqa
                              models.JOBDEFINITIONS.c.state != 'archived')}],
        'jobdefinition.tests': [
            {'right': models.JOIN_JOBDEFINITIONS_TESTS,
             'onclause': models.JOIN_JOBDEFINITIONS_TESTS.c.jobdefinition_id == models.JOBDEFINITIONS.c.id,  # noqa
             'isouter': True},
            {'right': JOBDEFINITION_TESTS,
             'onclause': and_(models.JOIN_JOBDEFINITIONS_TESTS.c.test_id == JOBDEFINITION_TESTS.c.id,  # noqa
                              JOBDEFINITION_TESTS.c.state != 'archived'),
             'isouter': True}],
        'remoteci': [
            {'right': REMOTECI,
             'onclause': and_(root_select.c.remoteci_id == REMOTECI.c.id,
                              REMOTECI.c.state != 'archived')}],
        'remoteci.tests': [
            {'right': models.JOIN_REMOTECIS_TESTS,
             'onclause': models.JOIN_REMOTECIS_TESTS.c.remoteci_id == REMOTECI.c.id,  # noqa
             'isouter': True},
            {'right': REMOTECI_TESTS,
             'onclause': and_(REMOTECI_TESTS.c.id == models.JOIN_REMOTECIS_TESTS.c.test_id,  # noqa
                              REMOTECI_TESTS.c.state != 'archived'),
             'isouter': True}],
        'components': [
            {'right': models.JOIN_JOBS_COMPONENTS,
             'onclause': models.JOIN_JOBS_COMPONENTS.c.job_id == root_select.c.id,  # noqa
             'isouter': True},
            {'right': models.COMPONENTS,
             'onclause': and_(models.COMPONENTS.c.id == models.JOIN_JOBS_COMPONENTS.c.component_id,  # noqa
                              models.COMPONENTS.c.state != 'archived'),
             'isouter': True}],
        'team': [
            {'right': TEAM,
             'onclause': and_(root_select.c.team_id == TEAM.c.id,
                              TEAM.c.state != 'archived')}]
    }


def remotecis(root_select=models.REMOTECIS):
    return {
        'team': [
            {'right': TEAM,
             'onclause': and_(TEAM.c.id == root_select.c.team_id,
                              TEAM.c.state != 'archived')}
        ],
        'lastjob': [
            {'right': LASTJOB,
             'onclause': and_(
                 LASTJOB.c.state != 'archived',
                 LASTJOB.c.status.in_([
                     'success',
                     'failure',
                     'killed',
                     'product-failure',
                     'deployment-failure']),
                 LASTJOB.c.remoteci_id == root_select.c.id),
             'isouter': True,
             'sort': LASTJOB.c.created_at}],
        'lastjob.components': [
            {'right': LASTJOB_JOIN_COMPONENTS,
             'onclause': LASTJOB_JOIN_COMPONENTS.c.job_id == LASTJOB.c.id,  # noqa
             'isouter': True},
            {'right': LASTJOB_COMPONENTS,
             'onclause': and_(LASTJOB_COMPONENTS.c.id == LASTJOB_JOIN_COMPONENTS.c.component_id,  # noqa
                              LASTJOB_COMPONENTS.c.state != 'archived'),
             'isouter': True}],
        'currentjob': [
            {'right': CURRENTJOB,
             'onclause': and_(
                 CURRENTJOB.c.state != 'archived',
                 CURRENTJOB.c.status.in_([
                     'new',
                     'pre-run',
                     'running']),
                 CURRENTJOB.c.remoteci_id == root_select.c.id),
             'isouter': True,
             'sort': CURRENTJOB.c.created_at}],
        'currentjob.components': [
            {'right': CURRENTJOB_JOIN_COMPONENTS,
             'onclause': CURRENTJOB_JOIN_COMPONENTS.c.job_id == CURRENTJOB.c.id,  # noqa
             'isouter': True},
            {'right': CURRENTJOB_COMPONENTS,
             'onclause': and_(CURRENTJOB_COMPONENTS.c.id == CURRENTJOB_JOIN_COMPONENTS.c.component_id,  # noqa
                              CURRENTJOB_COMPONENTS.c.state != 'archived'),
             'isouter': True}]
    }


def components(root_select=models.COMPONENTS):
    return {
        'files': [
            {'right': CFILES,
             'onclause': and_(
                 CFILES.c.component_id == root_select.c.id,
                 CFILES.c.state != 'archived'),
             'isouter': True
             }],
        'jobs': [
            {'right': models.JOIN_JOBS_COMPONENTS,
             'onclause': models.JOIN_JOBS_COMPONENTS.c.component_id == root_select.c.id,  # noqa
             'isouter': True},
            {'right': models.JOBS,
             'onclause': and_(models.JOBS.c.id == models.JOIN_JOBS_COMPONENTS.c.job_id,  # noqa
                              models.JOBS.c.state != 'archived'),
             'isouter': True}]
    }


def files(root_select=models.FILES):
    return {
        'jobstate': [
            {'right': JOBSTATE,
             'onclause': JOBSTATE.c.id == root_select.c.jobstate_id,
             'isouter': True}
        ],
        'jobstate.job': [
            {'right': JOBSTATE_JOBS,
             'onclause': JOBSTATE.c.job_id == JOBSTATE_JOBS.c.id,
             'isouter': True}],
        'job': [
            {'right': JOB,
             'onclause': root_select.c.job_id == JOB.c.id,
             'isouter': True}
        ],
        'team': [
            {'right': TEAM,
             'onclause': root_select.c.team_id == TEAM.c.id}
        ]
    }


# associate the name table to the object table
# used for select clause
EMBED_STRING_TO_OBJECT = {
    'jobs': {
        'files': models.FILES,
        'metas': models.METAS,
        'jobdefinition': models.JOBDEFINITIONS.alias('jobdefinition'),
        'jobdefinition.tests': JOBDEFINITION_TESTS,
        'remoteci': REMOTECI,
        'remoteci.tests': REMOTECI_TESTS,
        'components': models.COMPONENTS,
        'team': TEAM},
    'remotecis': {
        'team': TEAM,
        'lastjob': LASTJOB_WITHOUT_CONFIGURATION,
        'lastjob.components': LASTJOB_COMPONENTS,
        'currentjob': CURRENTJOB_WITHOUT_CONFIGURATION,
        'currentjob.components': CURRENTJOB_COMPONENTS},
    'components': {
        'files': CFILES,
        'jobs': JOBS_WITHOUT_CONFIGURATION},
    'files': {
        'jobstate': JOBSTATE,
        'jobstate.job': JOBSTATEJOBS_WITHOUT_CONFIGURATION,
        'job': JOB_WITHOUT_CONFIGURATION,
        'team': TEAM}
}


# for each table associate its embed's function handler
EMBED_JOINS = {
    'jobs': jobs,
    'remotecis': remotecis,
    'components': components,
    'files': files
}


import collections
Embed = collections.namedtuple('Embed', [
    'many', 'select', 'where', 'sort', 'join'])


def embed(many=False, select=None, where=None,
          sort=None, join=None):
    """Prepare a Embed named tuple

    :param many: True if it's a one-to-many join
    :param select: an optional list of field to embed
    :param where: an extra WHERE clause
    :param sort: an extra ORDER BY clause
    :param join: an SQLAlchemy-core Join instance
    """
    return Embed(many, select, where, sort, join)


def jobdefinitions():
    topic = models.TOPICS.alias('topic')
    return {
        'topic': embed(
            select=[topic],
            where=and_(
                models.JOBDEFINITIONS.c.topic_id == topic.c.id,
                topic.c.state != 'archived'
            ))}


def jobstates():
    team = models.TEAMS.alias('team')
    js0 = models.JOBSTATES.alias('js0')
    js1 = models.JOBSTATES.alias('js1')
    job = models.JOBS.alias('job')
    return {
        'files': embed(
            select=[models.FILES],
            join=js0.join(
                models.FILES,
                and_(
                    js0.c.id == models.FILES.c.jobstate_id,
                    models.FILES.c.state != 'archived'
                ),
                isouter=True),
            where=js0.c.id == models.JOBSTATES.c.id,
            many=True),
        'job': embed(
            select=[c for n, c in job.c.items() if n != 'configuration'],
            join=js1.join(
                job,
                and_(
                    sql.expression.or_(
                        js1.c.job_id == job.c.id,
                        job.c.id == None  # noqa
                    ),
                    job.c.state != 'archived',
                    ),
                isouter=True),
            where=js1.c.id == models.JOBSTATES.c.id,
            sort=job.c.created_at),
        'team': embed(
            select=[team],
            where=and_(
                models.JOBSTATES.c.team_id == team.c.id,
                team.c.state != 'archived'
            )
        )}


def teams():
    t0 = models.TEAMS.alias('t0')
    t1 = models.TEAMS.alias('t1')
    return {
        'topics': embed(
            select=[models.TOPICS],
            join=t0.join(
                models.JOINS_TOPICS_TEAMS.join(
                    models.TOPICS,
                    and_(
                        models.JOINS_TOPICS_TEAMS.c.topic_id ==
                        models.TOPICS.c.id,
                        models.TOPICS.c.state != 'archived'),
                    isouter=True),
                models.JOINS_TOPICS_TEAMS.c.team_id == t0.c.id,
                isouter=True
            ),
            where=t0.c.id == models.TEAMS.c.id,
            many=True),
        'remotecis': embed(
            select=[models.REMOTECIS],
            join=t1.join(
                models.REMOTECIS,
                and_(
                    models.REMOTECIS.c.state != 'archived',
                    models.REMOTECIS.c.team_id == models.TEAMS.c.id),
                isouter=True),
            where=t1.c.id == models.TEAMS.c.id,
            many=True)}


def tests():
    topics = models.TOPICS
    return {
        'topics': embed(
            select=[topics],
            join=models.TESTS.join(
                models.JOIN_TOPICS_TESTS.join(
                    topics,
                    and_(
                        topics.c.state != 'archived',
                        topics.c.id == models.JOIN_TOPICS_TESTS.c.topic_id
                    )),
                models.TESTS.c.id == models.JOIN_TOPICS_TESTS.c.test_id
            ))}


def topics():
    return {
        'teams': embed(
            select=[models.TEAMS],
            join=models.TOPICS.join(
                models.JOINS_TOPICS_TEAMS.join(
                    models.TEAMS,
                    and_(
                        models.TEAMS.c.state != 'archived',
                        models.JOINS_TOPICS_TEAMS.c.team_id ==
                        models.TEAMS.c.id),
                    isouter=True
                ),
                models.JOINS_TOPICS_TEAMS.c.topic_id == models.TOPICS.c.id,
                isouter=True),
            many=True)}


def users():
    team = models.TEAMS.alias('team')
    return {
        'team': embed(
            select=[team],
            where=and_(
                team.c.id == models.USERS.c.team_id,
                team.c.state != 'archived'
            ))}
