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
from sqlalchemy.sql import or_
from dci.api.v1 import utils as v1_utils


def components():
    component = models.COMPONENTS
    component_files = models.COMPONENT_FILES.alias('files')
    return {
        'files': v1_utils.embed(
            select=[component_files],
            join=component.join(
                component_files,
                component_files.c.component_id == component.c.id,
                isouter=True
            ),
            many=True),
    }


def files():
    team = models.TEAMS.alias('team')
    jobstate = models.JOBSTATES.alias('jobstate')
    jobstate_t = models.JOBSTATES.alias('jobstate_t')
    jobstate_job = models.JOBS.alias('jobstate.job')
    job = models.JOBS.alias('job')
    f0 = models.FILES.alias('f0')
    f1 = models.FILES.alias('f1')
    # f2 = models.FILES.alias('f2')
    return {
        'jobstate': v1_utils.embed(
            select=[jobstate],
            join=f0.join(
                jobstate,
                sql.expression.or_(
                    f0.c.jobstate_id == jobstate.c.id,
                    f0.c.jobstate_id == None))),  # noqa
        'jobstate.job': v1_utils.embed(
            select=[c
                    for n, c in jobstate_job.c.items()
                    if n != 'configuration'],
            join=jobstate_t.join(
                jobstate_job,
                sql.expression.or_(
                    jobstate_t.c.job_id == jobstate_job.c.id,
                    jobstate_job.c.id == None)),
            where=jobstate.c.id == jobstate_t.c.id),
        'job': v1_utils.embed(
            select=[job],
            join=f1.join(
                job,
                sql.expression.or_(
                    job.c.id == f1.c.job_id,
                    job.c.id == None)
                ),
            where=job.c.state != 'archived'),
        'team': v1_utils.embed(
            select=[team],
            where=and_(
                models.FILES.c.team_id == team.c.id,
                team.c.state != 'archived'
            )
        )
    }


def jobdefinitions():
    topic = models.TOPICS.alias('topic')
    return {
        'topic': v1_utils.embed(
            select=[topic],
            where=and_(
                models.JOBDEFINITIONS.c.topic_id == topic.c.id,
                topic.c.state != 'archived'
            ))}


def jobs():
    jobdefinition = models.JOBDEFINITIONS.alias('jobdefinition')
    jobdefinition_tests = models.TESTS.alias('jobdefinition.tests')
    team = models.TEAMS.alias('team')
    remoteci = models.REMOTECIS.alias('remoteci')
    remoteci_tests = models.TESTS.alias('remoteci.tests')
    j0 = models.JOBS.alias('j0')
    j1 = models.JOBS.alias('j1')
    j2 = models.JOBS.alias('j2')
    j3 = models.JOBS.alias('j3')
    j4 = models.JOBS.alias('j4')
    j5 = models.JOBS.alias('j5')
    return {
        'files': v1_utils.embed(
            select=[models.FILES],
            join=j0.join(
                models.FILES,
                and_(
                    j0.c.id == models.FILES.c.job_id,
                    models.FILES.c.state != 'archived'
                ),
                isouter=True),
            where=j0.c.id == models.JOBS.c.id,
            many=True),
        'jobdefinition': v1_utils.embed(
            select=[jobdefinition],
            join=j1.join(
                jobdefinition,
                and_(
                    j1.c.jobdefinition_id == jobdefinition.c.id,
                    jobdefinition.c.state != 'archived'
                )
            ),
            where=j1.c.id == models.JOBS.c.id),
        'jobdefinition.tests': v1_utils.embed(
            select=[jobdefinition_tests],
            join=j2.join(
                models.JOIN_JOBDEFINITIONS_TESTS.join(
                    jobdefinition_tests,
                    jobdefinition_tests.c.id ==
                    models.JOIN_JOBDEFINITIONS_TESTS.c.test_id,
                    isouter=True),
                models.JOIN_JOBDEFINITIONS_TESTS.c.jobdefinition_id ==
                j2.c.jobdefinition_id,
                isouter=True),
            where=j2.c.id == models.JOBS.c.id,
            many=True),
        'team': v1_utils.embed(
            select=[team],
            where=and_(
                models.JOBS.c.team_id == team.c.id,
                team.c.state != 'archived'
            ),
        ),
        'remoteci': v1_utils.embed(
            select=[remoteci],
            where=and_(
                models.JOBS.c.remoteci_id == remoteci.c.id,
                remoteci.c.state != 'archived'
            ),
        ),
        'remoteci.tests': v1_utils.embed(
            select=[remoteci_tests],
            join=j3.join(
                models.JOIN_REMOTECIS_TESTS.join(
                    remoteci_tests,
                    remoteci_tests.c.id ==
                    models.JOIN_REMOTECIS_TESTS.c.test_id,
                    isouter=True),
                j3.c.remoteci_id == models.JOIN_REMOTECIS_TESTS.c.remoteci_id,
                isouter=True
            ),
            where=j3.c.id == models.JOBS.c.id,
            many=True),
        'metas': v1_utils.embed(
            select=[models.METAS],
            join=j4.join(
                models.METAS,
                models.METAS.c.job_id == j4.c.id,
                isouter=True),
            where=j4.c.id == models.JOBS.c.id,
            many=True),
        'components': v1_utils.embed(
            select=[models.COMPONENTS],
            join=j5.join(
                models.JOIN_JOBS_COMPONENTS.join(
                    models.COMPONENTS,
                    and_(
                        models.COMPONENTS.c.id ==
                        models.JOIN_JOBS_COMPONENTS.c.component_id,
                        models.COMPONENTS.c.state != 'archived'
                    ),
                    isouter=True),
                models.JOIN_JOBS_COMPONENTS.c.job_id == j5.c.id,
                isouter=True),
            where=j5.c.id == models.JOBS.c.id,
            many=True)}


def jobstates():
    team = models.TEAMS.alias('team')
    js0 = models.JOBSTATES.alias('js0')
    js1 = models.JOBSTATES.alias('js1')
    job = models.JOBS.alias('job')
    return {
        'files': v1_utils.embed(
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
        'job': v1_utils.embed(
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
        'team': v1_utils.embed(
            select=[team],
            where=and_(
                models.JOBSTATES.c.team_id == team.c.id,
                team.c.state != 'archived'
            )
        )}


def remotecis():
    lj = models.JOBS.alias('last_job')
    cj = models.JOBS.alias('current_job')
    lj_components = models.COMPONENTS.alias('last_job.components')
    cj_components = models.COMPONENTS.alias('current_job.components')
    cjc = models.JOIN_JOBS_COMPONENTS.alias('cjc')
    ljc = models.JOIN_JOBS_COMPONENTS.alias('ljc')
    rci0 = models.REMOTECIS.alias('remoteci_0')
    rci1 = models.REMOTECIS.alias('remoteci_1')
    rci2 = models.REMOTECIS.alias('remoteci_2')
    rci3 = models.REMOTECIS.alias('remoteci_3')
    rci4 = models.REMOTECIS.alias('remoteci_4')
    lj_t = models.JOBS.alias('last_job_t')
    cj_t = models.JOBS.alias('current_job_t')
    team = models.TEAMS.alias('team')

    return {
        'team': v1_utils.embed(
            select=[team],
            join=rci0.join(team, and_(team.c.id == rci0.c.team_id,
                                      team.c.state != 'archived')),
            where=rci0.c.id == models.REMOTECIS.c.id),
        'last_job': v1_utils.embed(
            select=[c for n, c in lj.c.items() if n != 'configuration'],
            join=rci1.join(
                lj,
                and_(
                    lj.c.state != 'archived',
                    lj.c.remoteci_id == rci1.c.id,
                    lj.c.status.in_([
                        'success',
                        'failure',
                        'killed',
                        'product-failure',
                        'deployment-failure'])),
                isouter=True),
            where=rci1.c.id == models.REMOTECIS.c.id,
            sort=lj.c.created_at),
        'last_job.components': v1_utils.embed(
            select=[lj_components],
            join=rci2.join(
                lj_t.join(
                    ljc.join(
                        lj_components,
                        and_(
                            ljc.c.component_id == lj_components.c.id,
                            lj_components.c.state != 'archived'
                        ),
                        isouter=True),
                    and_(
                        ljc.c.job_id == lj_t.c.id,
                        lj_t.c.state != 'archived'
                    ),
                    isouter=True),
                lj_t.c.remoteci_id == rci2.c.id,
                isouter=True),
            where=and_(
                rci2.c.id == models.REMOTECIS.c.id,
                or_(
                    lj.c.id == lj_t.c.id,
                    lj.c.id == None)),
            many=True),
        'current_job': v1_utils.embed(
            select=[c for n, c in cj.c.items() if n != 'configuration'],
            join=rci3.join(
                cj,
                and_(
                    cj.c.state != 'archived',
                    cj.c.remoteci_id == rci3.c.id,
                    cj.c.status.in_([
                        'new',
                        'pre-run',
                        'running'])),
                isouter=True),
            where=rci3.c.id == models.REMOTECIS.c.id,
            sort=cj.c.created_at),
        'current_job.components': v1_utils.embed(
            select=[cj_components],
            join=rci4.join(
                cj_t.join(
                    cjc.join(
                        cj_components,
                        and_(
                            cjc.c.component_id == cj_components.c.id,
                            cj_components.c.state != 'archived'
                        ),
                        isouter=True),
                    and_(
                        cjc.c.job_id == cj_t.c.id,
                        cj_t.c.state != 'archived'
                    ),
                    isouter=True),
                cj_t.c.remoteci_id == rci4.c.id,
                isouter=True),
            where=and_(
                rci4.c.id == models.REMOTECIS.c.id,
                or_(
                    cj.c.id == cj_t.c.id,
                    cj.c.id == None)),  # noqa
            many=True)}


def teams():
    t0 = models.TEAMS.alias('t0')
    t1 = models.TEAMS.alias('t1')
    return {
        'topics': v1_utils.embed(
            select=[models.TOPICS],
            join=t0.join(
                models.JOINS_TOPICS_TEAMS.join(
                    models.TOPICS,
                    and_(
                        models.JOINS_TOPICS_TEAMS.c.topic_id ==
                        models.TOPICS.c.id,
                        models.TOPICS.c.state != 'archived',
                    ),
                    isouter=True),
                models.JOINS_TOPICS_TEAMS.c.team_id == t0.c.id,
                isouter=True
            ),
            where=t0.c.id == models.TEAMS.c.id,
            many=True),
        'remotecis': v1_utils.embed(
            select=[models.REMOTECIS],
            join=t1.join(
                models.REMOTECIS,
                and_(
                    models.REMOTECIS.c.state != 'archived',
                    models.REMOTECIS.c.team_id == models.TEAMS.c.id,
                ),
                isouter=True),
            where=t1.c.id == models.TEAMS.c.id,
            many=True)}


def tests():
    topics = models.TOPICS
    return {
        'topics': v1_utils.embed(
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
        'teams': v1_utils.embed(
            select=[models.TEAMS],
            join=models.TOPICS.join(
                models.JOINS_TOPICS_TEAMS.join(
                    models.TEAMS,
                    and_(
                        models.TEAMS.c.state != 'archived',
                        models.JOINS_TOPICS_TEAMS.c.team_id ==
                        models.TEAMS.c.id,
                    ),
                    isouter=True
                ),
                models.JOINS_TOPICS_TEAMS.c.topic_id == models.TOPICS.c.id,
                isouter=True),
            many=True)}


def users():
    team = models.TEAMS.alias('team')
    return {
        'team': v1_utils.embed(
            select=[team],
            where=and_(
                team.c.id == models.USERS.c.team_id,
                team.c.state != 'archived'
            ))}
