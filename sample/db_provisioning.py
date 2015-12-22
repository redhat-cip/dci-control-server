#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Red Hat, Inc
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

import datetime
from dci.server import auth
from dci.server.db import models
import dci.server.dci_config as config
import functools
import hashlib
import random
import sqlalchemy
import sqlalchemy_utils.functions
import sys
import time


COMPANIES = ['IBM', 'HP', 'DELL', 'Rackspace', 'Brocade', 'Redhat', 'Huawei',
             'Juniper', 'Comcast']

COMPONENT_TYPES = ['git', 'image', 'package', 'gerrit_review']

COMPONENTS = ['Khaleesi', 'RDO manager', 'OSP director', 'DCI-control-server']

TESTS = ['tempest', 'khaleesi-tempest', 'tox']

VERSIONS = ['v0.8', 'v2.1.1', 'v1.2.15', 'v0.4.2', 'v1.1', 'v2.5']

PROJECT_NAMES = ['Morbid Epsilon', 'Rocky Pluto', 'Timely Shower',
                 'Brave Drill', 'Sad Scissors']

REMOTE_CIS_ATTRS = {
    'storage': ['netapp', 'ceph', 'swift', 'AWS'],
    'network': ['Cisco', 'Juniper', 'HP', 'Brocade'],
    'hardware': ['Dell', 'Intel', 'HP', 'Huawei'],
    'virtualization': ['KVM', 'VMWare', 'Xen', 'Hyper-V']
}

NAMES = ['foobar', 'fubar', 'foo', 'bar', 'baz', 'qux', 'quux', 'norf']

JOB_STATUSES = ['new', 'pre-run', 'running', 'post-run', 'success', 'failure']

LOREM_IPSUM = [
    'Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
    'Donec a diam lectus. Sed sit amet ipsum mauris.',
    'Maecenas congue ligula ac quam viverra nec consectetur ante hendrerit.',
    'Donec et mollis dolor.',
    'Praesent et diam eget libero egestas mattis sit amet vitae augue.',
    'Nam tincidunt congue enim, ut porta lorem lacinia consectetur.',
    'Donec ut libero sed arcu vehicula ultricies a non tortor.',
    'Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
    'Aenean ut gravida lorem. Ut turpis felis, pulvinar a semper sed, '
    'adipiscing id dolor.',
    'Pellentesque auctor nisi id magna consequat sagittis.',
    'Curabitur dapibus enim sit amet elit pharetra tincidunt feugiat '
    'nisl imperdiet.',
    'Ut convallis libero in urna ultrices accumsan.',
    'Donec sed odio eros.',
    'Donec viverra mi quis quam pulvinar at malesuada arcu rhoncus.',
    'Cum sociis natoque penatibus et magnis dis parturient montes, '
    'nascetur ridiculus mus.',
    'In rutrum accumsan ultricies.',
    'Mauris vitae nisi at sem facilisis semper ac in est.'
]


def create_remote_cis(db_conn, company, tests):
    # create 3 remote CIS per company (one for each test)
    remote_cis = {}

    def generate_jd_names(test_name, job_definition_names):
        name = '%s %s %s' % (company['name'], test_name,
                             random.choice(VERSIONS))
        if len(job_definition_names) == 3:
            return job_definition_names
        if name not in job_definition_names:
            job_definition_names.append(name)

        return generate_jd_names(test_name, job_definition_names)

    def generate_data_field():
        data = {}
        for _ in range(0, random.randint(0, 10)):
            data_type = random.choice(list(REMOTE_CIS_ATTRS.keys()))
            data[data_type] = random.choice(REMOTE_CIS_ATTRS[data_type])
        return data

    for i, test_name in enumerate(tests):
        remote_ci = {
            'data': generate_data_field(),
            'team_id': company['id'],
            'name': '%s - %d' % (company['name'], i)
        }
        remote_ci = db_insert(db_conn, models.REMOTECIS, **remote_ci)
        job_definitions = []

        # create 3 job definitions for each test
        for job_definition_name in generate_jd_names(test_name, []):
            job_definition = {
                'name': job_definition_name,
                'priority': random.randint(0, 10) * 100,
                'test_id': tests[test_name]
            }
            job_definition['id'] = db_insert(db_conn, models.JOBDEFINITIONS,
                                             **job_definition)
            job_definitions.append(job_definition)

        remote_cis[remote_ci] = job_definitions

    return remote_cis


def create_jobs(db_conn, company_id, remote_cis):
    jobs = []
    for remote_ci, job_definitions in remote_cis.items():
        for job_definition in job_definitions:
            delta = datetime.timedelta(hours=random.randint(0, 10))
            since = datetime.timedelta(days=random.randint(0, 3),
                                       hours=random.randint(0, 10))
            job = {
                'remoteci_id': remote_ci,
                'jobdefinition_id': job_definition['id'],
                'created_at': datetime.datetime.now() - since - delta,
                'updated_at': datetime.datetime.now() - since,
                'status': random.choice(JOB_STATUSES),
                'team_id': company_id
            }
            job['id'] = db_insert(db_conn, models.JOBS, **job)
            jobs.append(job)

    return jobs


def create_jobdefinition_components(db_conn, components, job_definitions):
    for job_definition in job_definitions:

        # add between 1 and 5 components on the jobdefinition
        nb_components = random.randint(1, 5)
        for i in range(0, nb_components):
            db_insert(db_conn, models.JOIN_JOBDEFINITIONS_COMPONENTS,
                      jobdefinition_id=job_definition['id'],
                      component_id=components[i])


def create_files(db_conn, jobstate, company_id):
    def filename_generator():
        words = []
        for _ in range(0, random.randint(1, 4)):
            words.append(random.choice(NAMES))
        return '_'.join(words)

    for _ in range(0, random.randint(1, 4)):

        name = '%s.txt' % filename_generator()
        args = {
            'name': name,
            'content': lorem(),
            'mime': 'text/plain',
            'md5': hashlib.md5(name.encode('utf8')).hexdigest(),
            'jobstate_id': jobstate,
            'team_id': company_id
        }

        db_insert(db_conn, models.FILES, **args)


def create_jobstates_and_files(db_conn, job, company_id):
    job, job_def = job

    name = job_def['name']
    step = job['status']
    id = job['id']

    # create "new" jobstate do not create files
    db_insert(db_conn, models.JOBSTATES, status='new',
              comment='Job "%s" created' % name,
              job_id=id, team_id=company_id,
              created_at=job['created_at'])

    if step == 'new':
        return

    start, end  = job['created_at'], job['updated_at']
    start = time.mktime(start.timetuple())
    end = time.mktime(end.timetuple())

    step_number = JOB_STATUSES.index(step)

    # calculate timedelta for job running
    job_start = int(start + random.random() * (end - start))
    job_duration = end - job_start

    def compute_creation(current_step):
        step_index = JOB_STATUSES.index(current_step)
        creation = job_start +  (job_duration * step_index / step_number)
        return datetime.datetime.fromtimestamp(creation)

    # create "pre-run" jobstate and new files associated
    created_at = compute_creation('pre-run')
    jobstate = db_insert(db_conn, models.JOBSTATES, status='pre-run',
                         comment='initializing %s' % name,
                         job_id=id, team_id=company_id,
                         created_at=created_at, updated_at=created_at)
    create_files(db_conn, jobstate, company_id)

    if step == 'pre-run':
        return

    # create "running" jobstate
    created_at = compute_creation('running')
    jobstate = db_insert(db_conn, models.JOBSTATES, status='running',
                         comment='running %s...' % name,
                         job_id=id, team_id=company_id,
                         created_at=created_at, updated_at=created_at)
    create_files(db_conn, jobstate, company_id)

    if step == 'running':
        return

    # create "post-run" jobstate sometimes
    created_at = compute_creation('post-run')
    if random.random() > 0.7 and step != 'post-run':
        jobstate = db_insert(db_conn, models.JOBSTATES, status='post-run',
                             comment='finalizing %s...' % name,
                             job_id=id, team_id=company_id,
                             created_at=created_at, updated_at=created_at)

        create_files(db_conn, jobstate, company_id)

    if step == 'post-run':
        return

    # choose between "success", "failure" jobstate
    created_at = compute_creation('success')
    jobstate = db_insert(db_conn, models.JOBSTATES, status=job['status'],
                         comment='%s %s' % (name, step),
                         job_id=id, team_id=company_id,
                         created_at=created_at, updated_at=created_at)
    # no file creation on last state


def db_insert(db_conn, model_item, **kwargs):
    query = model_item.insert().values(**kwargs)
    return db_conn.execute(query).inserted_primary_key[0]


def lorem():
    nb = random.randint(1, len(LOREM_IPSUM))
    long_line = ' '.join(LOREM_IPSUM[0:7])

    return long_line + '\n'.join(LOREM_IPSUM[0:nb])


def init_db(db_conn):
    db_ins = functools.partial(db_insert, db_conn)

    components = []
    for component in COMPONENTS:
        component_type = random.choice(COMPONENT_TYPES)

        for i in range(0, 5):
            project = random.choice(PROJECT_NAMES)
            project_slug = '-'.join(project.lower().split())
            commit = (hashlib.sha1(str(random.random()).encode('utf8'))
                      .hexdigest())

            url = 'https://github.com/%s/commit/%s'
            attrs = {
                'name': component + '-%s' % i,
                'type': component_type,
                'canonical_project_name': '%s - %s' % (component, project),
                # This entry is basically a copy of the other fields,
                # this will may be removed in the future
                'data': {},
                'sha': commit,
                'title': project,
                'message': lorem(),
                'url': url % (project_slug, commit),
                'ref': ''
            }
            components.append(db_ins(models.COMPONENTS, **attrs))

    tests = {}
    for test in TESTS:
        tests[test] = db_ins(models.TESTS, name=test, data={})

    # Create the super admin user
    admin_team = db_ins(models.TEAMS, name='admin')

    db_ins(models.USERS, name='admin',
           role='admin',
           password=auth.hash_password('admin'),
           team_id=admin_team)

    # For each constructor create an admin and a user, cis and jobs
    for company in COMPANIES:
        c = {}
        c['name'] = company
        c['id'] = db_ins(models.TEAMS, name=company)

        user = {'name': '%s_user' % (company.lower(),),
                'password': auth.hash_password(company), 'team_id': c['id']}
        admin = {'name': '%s_admin' % (company.lower(),),
                 'password': auth.hash_password(company), 'team_id': c['id']}

        c['user'] = db_ins(models.USERS, **user)
        c['admin'] = db_ins(models.USERS, **admin)

        remote_cis = create_remote_cis(db_conn, c, tests)
        jobs = create_jobs(db_conn, c['id'], remote_cis)
        # flatten job_definitions
        job_definitions = [jd for jds in remote_cis.values() for jd in jds]
        create_jobdefinition_components(db_conn, components, job_definitions)
        for job in zip(jobs, job_definitions):
            create_jobstates_and_files(db_conn, job, c['id'])


if __name__ == '__main__':
    conf = config.generate_conf()
    db_uri = conf['SQLALCHEMY_DATABASE_URI']

    if sqlalchemy_utils.functions.database_exists(db_uri):
        while True:
            print('Be carefull this script will override your database:')
            print(db_uri)
            print('')
            i = raw_input('Continue ? [y/N] ').lower()
            if not i or i == 'n':
                sys.exit(0)
            if i == 'y':
                break

        sqlalchemy_utils.functions.drop_database(db_uri)

    sqlalchemy_utils.functions.create_database(db_uri)

    engine = sqlalchemy.create_engine(db_uri)
    models.metadata.create_all(engine)
    with engine.begin() as conn:
        init_db(conn)
