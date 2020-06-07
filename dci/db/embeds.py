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

from sqlalchemy.sql import and_


def ignore_columns_from_table(table, ignored_columns):
    return [getattr(table.c, column.name)
            for column in table.columns
            if column.name not in ignored_columns]

# These functions should be called by v1_utils.QueryBuilder


# Create necessary aliases
TEAM = models.TEAMS.alias('team')
PRODUCT = models.PRODUCTS.alias('product')
REMOTECI = models.REMOTECIS.alias('remoteci')
CFILES = models.COMPONENT_FILES.alias('files')

TESTS_RESULTS = models.TESTS_RESULTS.alias('results')
JOB = models.JOBS.alias('job')

JOBSTATE = models.JOBSTATES.alias('jobstate')
JOBSTATE_JOBS = models.JOBS.alias('jobstate.job')

TOPIC = models.TOPICS.alias('topic')
NEXT_TOPIC = models.TOPICS.alias('next_topic')

JOIN_USERS_TEAMS = models.JOIN_USERS_TEAMS.alias('join_users_teams')  # noqa


def jobs(root_select=models.JOBS):
    return {
        'files': [
            {'right': models.FILES,
             'onclause': and_(models.FILES.c.job_id == root_select.c.id,
                              models.FILES.c.state != 'archived'),
             'isouter': True}],
        'jobstates': [
            {'right': models.JOBSTATES,
             'onclause': models.JOBSTATES.c.job_id == root_select.c.id,
             'isouter': True}],
        'topic': [
            {'right': TOPIC,
             'onclause': and_(root_select.c.topic_id == TOPIC.c.id,
                              TOPIC.c.state != 'archived')}],
        'remoteci': [
            {'right': REMOTECI,
             'onclause': and_(root_select.c.remoteci_id == REMOTECI.c.id,
                              REMOTECI.c.state != 'archived')}],
        'components': [
            {'right': models.JOIN_JOBS_COMPONENTS,
             'onclause': models.JOIN_JOBS_COMPONENTS.c.job_id == root_select.c.id,  # noqa
             'isouter': True},
            {'right': models.COMPONENTS,
             'onclause': and_(models.COMPONENTS.c.id == models.JOIN_JOBS_COMPONENTS.c.component_id,  # noqa
                              models.COMPONENTS.c.topic_id == root_select.c.topic_id,  # noqa
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
        'issues': [
            {'right': models.JOIN_JOBS_ISSUES,
             'onclause': models.JOIN_JOBS_ISSUES.c.job_id == root_select.c.id,  # noqa
             'isouter': True},
            {'right': models.ISSUES,
             'onclause': and_(models.ISSUES.c.id == models.JOIN_JOBS_ISSUES.c.issue_id),  # noqa
             'isouter': True}],
        'analytics': [
            {'right': models.ANALYTICS,
             'onclause': models.ANALYTICS.c.job_id == root_select.c.id,
             'isouter': True}],
        'tags': [
            {'right': models.JOIN_JOBS_TAGS,
             'onclause': models.JOIN_JOBS_TAGS.c.job_id == root_select.c.id,
             'isouter': True},
            {'right': models.TAGS,
             'onclause': models.TAGS.c.id == models.JOIN_JOBS_TAGS.c.tag_id,  # noqa
             'isouter': True}]
    }


def remotecis(root_select=models.REMOTECIS):
    return {
        'team': [
            {'right': TEAM,
             'onclause': and_(TEAM.c.id == root_select.c.team_id,
                              TEAM.c.state != 'archived')}
        ]
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
        'topics': [
            {'right': models.TOPICS,
             'onclause': and_(models.TOPICS.c.product_id == root_select.c.id,
                              models.TOPICS.c.state != 'archived'),
             'isouter': True}],
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
        'next_topic': [
            {'right': NEXT_TOPIC,
             'onclause': and_(root_select.c.next_topic_id == NEXT_TOPIC.c.id,
                              NEXT_TOPIC.c.state != 'archived'),
             'isouter': True}],
    }


def users(root_select=models.USERS):
    return {
        'team': [
            {'right': JOIN_USERS_TEAMS,
             'onclause': JOIN_USERS_TEAMS.c.user_id == root_select.c.id,
             'isouter': True},
            {'right': TEAM,
             'onclause': and_(TEAM.c.id == JOIN_USERS_TEAMS.c.team_id,
                              TEAM.c.state != 'archived'),
             'isouter': True}
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
        'topic': TOPIC,
        'issues': models.ISSUES,
        'jobstates': models.JOBSTATES,
        'remoteci': REMOTECI,
        'components': models.COMPONENTS,
        'team': TEAM,
        'results': TESTS_RESULTS,
        'analytics': models.ANALYTICS,
        'tags': models.TAGS
    },
    'remotecis': {
        'team': TEAM},
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
        'job': JOB
    },
    'products': {
        'topics': models.TOPICS,
    },
    'teams': {
        'remotecis': models.REMOTECIS,
        'topics': models.TOPICS
    },
    'topics': {
        'teams': models.TEAMS,
        'product': PRODUCT,
        'next_topic': NEXT_TOPIC
    },
    'users': {
        'team': TEAM,
        'remotecis': models.REMOTECIS
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
    'teams': teams,
    'topics': topics,
    'users': users
}
