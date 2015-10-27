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

import bcrypt
import dci.server.app as app
import dci.server.db.models_core as models
import functools
import hashlib
import random
import sqlalchemy
import sqlalchemy_utils.functions
import sys


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
        name = '%s %s' % (test_name, random.choice(VERSIONS))
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
            jobs.append(db_insert(db_conn, models.JOBS, remoteci_id=remote_ci,
                                  jobdefinition_id=job_definition['id'],
                                  team_id=company_id))
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
    job_id, job = job
    # create "new" jobstate do not create files
    db_insert(db_conn, models.JOBSTATES, status='new',
              comment='Job "%s" created' % (job['name'],), job_id=job_id,
              team_id=company_id)

    # create "initializing" jobstate and new files associated
    for i in range(0, random.randint(1, 4)):
        jobstate = db_insert(db_conn, models.JOBSTATES, status='initializing',
                             comment='initializing step %d' % (i,),
                             job_id=job_id, team_id=company_id)
        create_files(db_conn, jobstate, company_id)

    # create "ongoing" jobstate
    for i in range(0, random.randint(1, 6)):
        jobstate = db_insert(db_conn, models.JOBSTATES, status='ongoing',
                             comment='running step %d...' % (i,),
                             job_id=job_id, team_id=company_id)
        create_files(db_conn, jobstate, company_id)

    # choose between "success", "failure", "killed", and "unfinished" jobstate
    status = random.choice(['success', 'failure', 'killed', 'unfinished'])
    jobstate = db_insert(db_conn, models.JOBSTATES, status=status,
                         comment='%s %s' % (job['name'], status),
                         job_id=job_id, team_id=company_id)
    create_files(db_conn, jobstate, company_id)


def db_insert(db_conn, model_item, **kwargs):
    query = model_item.insert().values(**kwargs)
    return db_conn.execute(query).inserted_primary_key[0]


def lorem():
    nb = random.randint(1, len(LOREM_IPSUM))
    return '\n'.join(LOREM_IPSUM[0:nb])


def passwd(passwd_str):
    return (bcrypt
            .hashpw(passwd_str.encode('utf-8'), bcrypt.gensalt())
            .decode('utf-8'))


def init_db(db_conn):
    db_ins = functools.partial(db_insert, db_conn)

    component_types = []
    for component_type in COMPONENT_TYPES:
        component_types.append(db_ins(models.COMPONENTYPES,
                                      name=component_type))

    components = []
    for component in COMPONENTS:
        component_type = random.choice(component_types)

        for _ in range(0, 5):
            project = random.choice(PROJECT_NAMES)
            project_slug = '-'.join(project.lower().split())
            commit = (hashlib.sha1(str(random.random()).encode('utf8'))
                      .hexdigest())

            url = 'https://github.com/%s/commit/%s'
            attrs = {
                'name': component,
                'componenttype_id': component_type,
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

    # Create roles
    admin_role = db_ins(models.ROLES, name='admin')
    user_role = db_ins(models.ROLES, name='user')

    # Create the super admin user
    admin_team = db_ins(models.TEAMS, name='admin')

    admin = db_ins(models.USERS, name='admin', password=passwd('admin'),
                   team_id=admin_team)

    db_ins(models.JOIN_USERS_ROLES, user_id=admin, role_id=admin_role)

    # For each constructor create an admin and a user, cis and jobs
    for company in COMPANIES:
        c = {}
        c['name'] = company
        c['id'] = db_ins(models.TEAMS, name=company)

        user = {'name': '%s_user' % (company.lower(),),
                'password': passwd(company), 'team_id': c['id']}
        admin = {'name': '%s_admin' % (company.lower(),),
                 'password': passwd(company), 'team_id': c['id']}

        c['user'] = db_ins(models.USERS, **user)
        c['admin'] = db_ins(models.USERS, **admin)

        db_ins(models.JOIN_USERS_ROLES, user_id=c['user'],
               role_id=user_role)
        db_ins(models.JOIN_USERS_ROLES, user_id=c['admin'],
               role_id=admin_role)

        remote_cis = create_remote_cis(db_conn, c, tests)
        jobs = create_jobs(db_conn, c['id'], remote_cis)
        # flatten job_definitions
        job_definitions = [jd for jds in remote_cis.values() for jd in jds]
        create_jobdefinition_components(db_conn, components, job_definitions)
        for job in zip(jobs, job_definitions):
            create_jobstates_and_files(db_conn, job, c['id'])


if __name__ == '__main__':
    conf = app.generate_conf()
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
    with engine.begin() as conn:
        conn.execute(models.pg_gen_uuid)

    models.metadata.create_all(engine)
    with engine.begin() as conn:
        init_db(conn)
