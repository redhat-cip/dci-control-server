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


# These functions should be called by v1_utils.QueryBuilder

# Create necessary aliases
REMOTECI_TESTS = models.TESTS.alias('remoteci.tests')
JOBDEFINITION_TESTS = models.TESTS.alias('jobdefinition.tests')


def jobs(root_select):
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
             'onclause': and_(root_select.c.jobdefinition_id == models.JOBDEFINITIONS.c.id,
                              models.JOBDEFINITIONS.c.state != 'archived')}],
        'jobdefinition.tests': [
            {'right': models.JOIN_JOBDEFINITIONS_TESTS,
             'onclause': models.JOIN_JOBDEFINITIONS_TESTS.c.jobdefinition_id == models.JOBDEFINITIONS.c.id,
             'isouter': True},
            {'right': JOBDEFINITION_TESTS,
             'onclause': and_(models.JOIN_JOBDEFINITIONS_TESTS.c.test_id == JOBDEFINITION_TESTS.c.id,
                              JOBDEFINITION_TESTS.c.state != 'archived'),
             'isouter': True}],
        'remoteci': [
            {'right': models.REMOTECIS,
             'onclause': and_(root_select.c.remoteci_id == models.REMOTECIS.c.id,
                              models.REMOTECIS.c.state != 'archived')}],
        'remoteci.tests': [
            {'right': models.JOIN_REMOTECIS_TESTS,
             'onclause': models.JOIN_REMOTECIS_TESTS.c.remoteci_id == models.REMOTECIS.c.id,
             'isouter': True},
            {'right': REMOTECI_TESTS,
             'onclause': and_(REMOTECI_TESTS.c.id == models.JOIN_REMOTECIS_TESTS.c.test_id,
                              REMOTECI_TESTS.c.state != 'archived'),
             'isouter': True}],
        'components': [
            {'right': models.JOIN_JOBS_COMPONENTS,
             'onclause': models.JOIN_JOBS_COMPONENTS.c.job_id == root_select.c.id,
             'isouter': True},
            {'right': models.COMPONENTS,
             'onclause': and_(models.COMPONENTS.c.id == models.JOIN_JOBS_COMPONENTS.c.component_id,
                              models.COMPONENTS.c.state != 'archived'),
             'isouter': True}],
        'team': [
            {'right': models.TEAMS,
             'onclause': and_(root_select.c.team_id == models.TEAMS.c.id,
                              models.TEAMS.c.state != 'archived')}]
    }


# associate the name table to the object table
EMBED_STRING_TO_OBJECT = {
    'files': models.FILES,
    'metas': models.METAS,
    'jobdefinition': models.JOBDEFINITIONS,
    'jobdefinition.tests': JOBDEFINITION_TESTS,
    'remoteci': models.REMOTECIS,
    'remoteci.tests': REMOTECI_TESTS,
    'components': models.COMPONENTS,
    'team': models.TEAMS
}

# for each table associate its embed function handler
EMBED_JOINS = {
    'jobs': jobs
}
