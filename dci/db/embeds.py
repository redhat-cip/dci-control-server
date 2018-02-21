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
TOPIC_TESTS = models.TESTS.alias('topic.tests')
TEAM = models.TEAMS.alias('team')
PRODUCT = models.PRODUCTS.alias('product')
REMOTECI = models.REMOTECIS.alias('remoteci')
CFILES = models.COMPONENT_FILES.alias('files')
RCONFIGURATION = models.REMOTECIS_RCONFIGURATIONS.alias('rconfiguration')

# ignore tests_cases as its too heavy to be embeded by jobs
TESTS_RESULTS = sql.select(ignore_columns_from_table(models.TESTS_RESULTS,
                                                     ['tests_cases']))
TESTS_RESULTS = TESTS_RESULTS.alias('results')
JOB = models.JOBS.alias('job')
LASTJOB = models.JOBS.alias('lastjob')
LASTJOB_COMPONENTS = models.COMPONENTS.alias('lastjob.components')
LASTJOB_JOIN_COMPONENTS = models.JOIN_JOBS_COMPONENTS.alias('lastjob.jobcomponents')  # noqa

CURRENTJOB = models.JOBS.alias('currentjob')
CURRENTJOB_COMPONENTS = models.COMPONENTS.alias('currentjob.components')
CURRENTJOB_JOIN_COMPONENTS = models.JOIN_JOBS_COMPONENTS.alias('currentjob.jobcomponents')  # noqa

JOBSTATE = models.JOBSTATES.alias('jobstate')
JOBSTATE_JOBS = models.JOBS.alias('jobstate.job')

TOPIC = models.TOPICS.alias('topic')
NEXT_TOPIC = models.TOPICS.alias('nexttopic')

ROLE = models.ROLES.alias('role')


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
        'jobstates': [
            {'right': models.JOBSTATES,
             'onclause': models.JOBSTATES.c.job_id == root_select.c.id,
             'isouter': True}],
        'topic': [
            {'right': TOPIC,
             'onclause': and_(root_select.c.topic_id == TOPIC.c.id,
                              TOPIC.c.state != 'archived')}],
        'topic.tests': [
            {'right': models.JOIN_TOPICS_TESTS,
             'onclause': models.JOIN_TOPICS_TESTS.c.topic_id == TOPIC.c.id,
             'isouter': True},
            {'right': TOPIC_TESTS,
             'onclause': and_(models.JOIN_TOPICS_TESTS.c.test_id == TOPIC_TESTS.c.id,  # noqa
                              TOPIC_TESTS.c.state != 'archived'),
             'isouter': True}
        ],
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
                              TEAM.c.state != 'archived')}],
        'results': [
            {'right': TESTS_RESULTS,
             'onclause': TESTS_RESULTS.c.job_id == root_select.c.id,
             'isouter': True}],
        'rconfiguration': [
            {'right': RCONFIGURATION,
             'onclause': and_(root_select.c.rconfiguration_id == RCONFIGURATION.c.id,  # noqa
                              RCONFIGURATION.c.state != 'archived'),
             'isouter': True}],
        'issues': [
            {'right': models.JOIN_JOBS_ISSUES,
             'onclause': models.JOIN_JOBS_ISSUES.c.job_id == root_select.c.id,  # noqa
             'isouter': True},
            {'right': models.ISSUES,
             'onclause': and_(models.ISSUES.c.id == models.JOIN_JOBS_ISSUES.c.issue_id),  # noqa
             'isouter': True}]
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


def jobstates(root_select=models.JOBSTATES):
    return {
        'files': [
            {'right': models.FILES,
             'onclause': and_(models.FILES.c.jobstate_id == root_select.c.id,
                              models.FILES.c.state != 'archived'),
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


def teams(root_select=models.TEAMS):
    return {
        'topics': [
            {'right': models.JOINS_TOPICS_TEAMS,
             'onclause': models.JOINS_TOPICS_TEAMS.c.team_id == root_select.c.id,  # noqa
             'isouter': True},
            {'right': models.TOPICS,
             'onclause': and_(models.TOPICS.c.id == models.JOINS_TOPICS_TEAMS.c.topic_id,  # noqa
                              models.TOPICS.c.state != 'archived'),
             'isouter': True}],
        'remotecis': [
            {'right': models.REMOTECIS,
             'onclause': and_(models.REMOTECIS.c.team_id == root_select.c.id,
                              models.REMOTECIS.c.state != 'archived'),
             'isouter': True}]
    }


def tests(root_select=models.TESTS):
    return {
        'topics': [
            {'right': models.JOIN_TOPICS_TESTS,
             'onclause': models.JOIN_TOPICS_TESTS.c.test_id == root_select.c.id,  # noqa
             'isouter': True},
            {'right': models.TOPICS,
             'onclause': and_(models.TOPICS.c.id == models.JOIN_TOPICS_TESTS.c.topic_id,  # noqa
                              models.TOPICS.c.state != 'archived'),
             'isouter': True}]
    }


def feeders(root_select=models.FEEDERS):
    return {
        'team': [
            {'right': TEAM,
             'onclause': and_(TEAM.c.id == root_select.c.team_id,
                              TEAM.c.state != 'archived')}
        ]
    }


def products(root_select=models.PRODUCTS):
    return {
        'team': [
            {'right': TEAM,
             'onclause': and_(TEAM.c.id == root_select.c.team_id,
                              TEAM.c.state != 'archived')}
        ],
        'topics': [
            {'right': models.TOPICS,
             'onclause': and_(models.TOPICS.c.product_id == root_select.c.id,
                              models.TOPICS.c.state != 'archived'),
             'isouter': True}],
    }


def roles(root_select=models.ROLES):
    return {
        'permissions': [
            {'right': models.JOIN_ROLES_PERMISSIONS,
             'onclause': models.JOIN_ROLES_PERMISSIONS.c.role_id == root_select.c.id,  # noqa
             'isouter': True},
            {'right': models.PERMISSIONS,
             'onclause': and_(models.PERMISSIONS.c.id == models.JOIN_ROLES_PERMISSIONS.c.permission_id,  # noqa
                              models.PERMISSIONS.c.state != 'archived'),
             'isouter': True}]
    }


def topics(root_select=models.TOPICS):
    return {
        'teams': [
            {'right': models.JOINS_TOPICS_TEAMS,
             'onclause': models.JOINS_TOPICS_TEAMS.c.topic_id == root_select.c.id,  # noqa
             'isouter': True},
            {'right': models.TEAMS,
             'onclause': and_(models.TEAMS.c.id == models.JOINS_TOPICS_TEAMS.c.team_id,  # noqa
                              models.TEAMS.c.state != 'archived'),
             'isouter': True}],
        'product': [
            {'right': PRODUCT,
             'onclause': and_(PRODUCT.c.id == root_select.c.product_id,
                              PRODUCT.c.state != 'archived'),
             'isouter': True}],
        'nexttopic': [
            {'right': NEXT_TOPIC,
             'onclause': and_(root_select.c.next_topic == NEXT_TOPIC.c.id,
                              NEXT_TOPIC.c.state != 'archived'),
             'isouter': True}],
    }


def users(root_select=models.USERS):
    return {
        'team': [
            {'right': TEAM,
             'onclause': and_(TEAM.c.id == root_select.c.team_id,
                              TEAM.c.state != 'archived'),
             'isouter': True}
        ],
        'role': [
            {'right': ROLE,
             'onclause': and_(ROLE.c.id == root_select.c.role_id,
                              ROLE.c.state != 'archived')}
        ],
        'remotecis': [
            {'right': models.JOIN_USER_REMOTECIS,
             'onclause': models.JOIN_USER_REMOTECIS.c.user_id == root_select.c.id,  # noqa
             'isouter': True},
            {'right': models.REMOTECIS,
             'onclause': and_(models.REMOTECIS.c.id == models.JOIN_USER_REMOTECIS.c.remoteci_id,  # noqa
                              models.REMOTECIS.c.state != 'archived'),
             'isouter': True}]
    }


# associate the name table to the object table
# used for select clause
EMBED_STRING_TO_OBJECT = {
    'jobs': {
        'files': models.FILES,
        'metas': models.METAS,
        'topic': TOPIC,
        'topic.tests': TOPIC_TESTS,
        'issues': models.ISSUES,
        'jobstates': models.JOBSTATES,
        'remoteci': REMOTECI,
        'remoteci.tests': REMOTECI_TESTS,
        'components': models.COMPONENTS,
        'team': TEAM,
        'results': TESTS_RESULTS,
        'rconfiguration': RCONFIGURATION,
    },
    'remotecis': {
        'team': TEAM,
        'lastjob': LASTJOB,
        'lastjob.components': LASTJOB_COMPONENTS,
        'currentjob': CURRENTJOB,
        'currentjob.components': CURRENTJOB_COMPONENTS},
    'components': {
        'files': CFILES,
        'jobs': models.JOBS},
    'feeders': {
        'team': TEAM},
    'files': {
        'jobstate': JOBSTATE,
        'jobstate.job': JOBSTATE_JOBS,
        'job': JOB,
        'team': TEAM},
    'jobstates': {
        'files': models.FILES,
        'job': JOB,
        'team': TEAM
    },
    'products': {
        'team': TEAM,
        'topics': models.TOPICS,
    },
    'roles': {
        'permissions': models.PERMISSIONS,
    },
    'teams': {
        'remotecis': models.REMOTECIS,
        'topics': models.TOPICS
    },
    'tests': {
        'topics': models.TOPICS
    },
    'topics': {
        'teams': models.TEAMS,
        'product': PRODUCT,
        'nexttopic': NEXT_TOPIC
    },
    'users': {
        'team': TEAM,
        'role': ROLE,
        'remotecis': models.REMOTECIS,
    }
}


# for each table associate its embed's function handler
EMBED_JOINS = {
    'jobs': jobs,
    'remotecis': remotecis,
    'components': components,
    'feeders': feeders,
    'files': files,
    'jobstates': jobstates,
    'products': products,
    'roles': roles,
    'teams': teams,
    'tests': tests,
    'topics': topics,
    'users': users
}
