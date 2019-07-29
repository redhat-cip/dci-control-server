# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Red Hat, Inc
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
from dci.api.v1.global_status import add_percentage_of_success
from dci.api.v1.global_status import format_global_status
from dci.api.v1.global_status import insert_component_with_no_job


def test_global_status(admin, user, job_user_id):
    user.post('/api/v1/jobstates',
              data={'job_id': job_user_id, 'status': 'success'})
    global_status = admin.get('/api/v1/global_status').data['globalStatus']
    assert global_status[0]['jobs'][0]['status'] == 'success'
    assert 'topic_name' in global_status[0]
    assert 'name' in global_status[0]
    assert global_status[0]['percentageOfSuccess'] == 100


def test_insert_component_with_no_job():

    jobs = [{
        'id': 'db37582a-43d9-72d7-afda-1ce481e2081b',
        'team_name': 'team_1',
        'remoteci_name': 'remoteci_1',
        'state': 'succes',
        'created_at': '2018-02-08T15:23:32.316227'
    }]
    components = [{
        'id': '48dd507a-8185-47de-aed1-ee41aefd1479',
        'name': 'component_1',
        'topic_name': 'topic_1',
        'product_name': 'product_1',
        'jobs': jobs
    }]

    latest_components = [
        {
            'id': '48dd507a-8185-47de-aed1-ee41aefd1479',
            'name': 'component_1',
            'topic_name': 'topic_1',
            'product_name': 'product_1'
        },
        {
            'id': '72d7582a-db37-43d9-afda-1ce481e2081b',
            'name': 'component_2',
            'topic_name': 'topic_2',
            'product_name': 'product_2'
        }
    ]

    components = insert_component_with_no_job(components, latest_components)

    assert len(components) == 2
    assert sorted(['topic_1', 'topic_2']) == \
        sorted([c['topic_name'] for c in components])
    assert sorted([[], jobs]) == sorted([c['jobs'] for c in components])


def test_format_global_status():
    jobs = [
        {
            'team_name': 'team 1',
            'remoteci_name': 'remoteci 1',
            'remoteci_id': '48dd507a-8185-47de-aed1-ee41aefd1479',
            'topic_name': 'topic A',
            'product_name': 'product A',
            'created_at': '2018-02-08T15:23:32.316227',
            'status': 'success',
            'component_name': 'component A',
            'component_id': '72d7582a-db37-43d9-afda-1ce481e2081b',
            'id': 'afda582a-db37-72d7-43d9-1ce481e2081b'
        },
        {
            'team_name': 'team 2',
            'remoteci_name': 'remoteci 2',
            'remoteci_id': 'aed1507a-8185-48dd-47de-ee41aefd1479',
            'topic_name': 'topic B',
            'product_name': 'product B',
            'created_at': '2018-02-08T15:23:32.316227',
            'status': 'failure',
            'component_name': 'component B',
            'component_id': '43d9582a-db37-72d7-afda-1ce481e2081b',
            'id': '43d9582a-db37-72d7-afda-1ce481e2081b'
        },
        {
            'team_name': 'team 3',
            'remoteci_name': 'remoteci 3',
            'remoteci_id': '8185507a-47de-48dd-aed1-ee41aefd1479',
            'topic_name': 'topic A',
            'product_name': 'product A',
            'created_at': '2018-02-08T15:23:32.316227',
            'status': 'success',
            'component_name': 'component A',
            'component_id': '72d7582a-db37-43d9-afda-1ce481e2081b',
            'id': 'db37582a-43d9-72d7-afda-1ce481e2081b'
        },
    ]
    global_status = sorted(format_global_status(jobs),
                           key=lambda x: x['id'], reverse=True)
    assert len(global_status) == 2

    component_a = global_status[0]
    assert component_a['id'] == '72d7582a-db37-43d9-afda-1ce481e2081b'
    assert component_a['name'] == 'component A'
    assert component_a['topic_name'] == 'topic A'
    assert component_a['product_name'] == 'product A'
    assert len(component_a['jobs']) == 2
    assert component_a['jobs'][0]['remoteci_name'] == 'remoteci 1'


def test_add_percentage_of_success():
    global_status = [
        {'jobs': [{'status': 'success'}, {'status': 'success'}]},
        {'jobs': [{'status': 'success'}, {'status': 'failure'}]},
        {'jobs': []},
    ]
    global_status_with_percentage = add_percentage_of_success(global_status)
    assert global_status_with_percentage[0]['percentageOfSuccess'] == 100
    assert global_status_with_percentage[1]['percentageOfSuccess'] == 50
    assert global_status_with_percentage[2]['percentageOfSuccess'] == 0
