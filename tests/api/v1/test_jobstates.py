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

from __future__ import unicode_literals

import tests.api.v1.test_files as files
import tests.utils as t_utils

import mock
import uuid


def test_create_jobstates(user, job_user_id):
    data = {'job_id': job_user_id, 'status': 'running', 'comment': 'kikoolol'}

    with mock.patch('dci.api.v1.notifications') as mocked_notif:
        js = user.post('/api/v1/jobstates', data=data).data
        assert not mocked_notif.displatcher.called
    js_id = js['jobstate']['id']

    js = user.get('/api/v1/jobstates/%s' % js_id).data
    job = user.get('/api/v1/jobs/%s' % job_user_id).data

    assert js['jobstate']['comment'] == 'kikoolol'
    assert job['job']['status'] == 'running'


def test_create_jobstates_failure(user, job_user_id):
    data = {'job_id': job_user_id, 'status': 'failure'}

    with mock.patch('dci.api.v1.notifications') as mocked_notif:
        user.post('/api/v1/jobstates', data=data).data
        # Notification should be sent just one time
        user.post('/api/v1/jobstates', data=data).data
        assert mocked_notif.dispatcher.called_once()

    job = user.get('/api/v1/jobs/%s' % job_user_id).data
    assert job['job']['status'] == 'failure'


def test_create_jobstates_empty_comment(user, job_user_id):
    data = {'job_id': job_user_id, 'status': 'running'}

    js = user.post('/api/v1/jobstates', data=data).data
    assert js['jobstate']['comment'] is None

    js = user.get('/api/v1/jobstates/%s' % js['jobstate']['id']).data
    assert js['jobstate']['comment'] is None


def test_get_all_jobstates(user, job_user_id):
    js_1 = user.post('/api/v1/jobstates',
                     data={'job_id': job_user_id,
                           'status': 'running', 'comment': 'kikoolol1'}).data
    js_1_id = js_1['jobstate']['id']

    js_2 = user.post('/api/v1/jobstates',
                     data={'job_id': job_user_id,
                           'status': 'running', 'comment': 'kikoolol2'}).data
    js_2_id = js_2['jobstate']['id']

    db_all_js = user.get('/api/v1/jobstates?sort=created_at').data
    db_all_js = db_all_js['jobstates']
    db_all_js_ids = [db_js['id'] for db_js in db_all_js]

    assert db_all_js_ids == [js_1_id, js_2_id]


def test_get_all_jobstates_with_pagination(user, job_user_id):
    # create 4 jobstates types and check meta count
    data = {'job_id': job_user_id, 'status': 'running',
            'comment': 'kikoolol1'}
    user.post('/api/v1/jobstates', data=data)
    data = {'job_id': job_user_id, 'status': 'running',
            'comment': 'kikoolol2'}
    user.post('/api/v1/jobstates', data=data)
    data = {'job_id': job_user_id, 'status': 'running',
            'comment': 'kikoolol3'}
    user.post('/api/v1/jobstates', data=data)
    data = {'job_id': job_user_id, 'status': 'running',
            'comment': 'kikoolol4'}
    user.post('/api/v1/jobstates', data=data)

    # check meta count
    js = user.get('/api/v1/jobstates').data
    assert js['_meta']['count'] == 4

    # verify limit and offset are working well
    js = user.get('/api/v1/jobstates?limit=2&offset=0').data
    assert len(js['jobstates']) == 2

    js = user.get('/api/v1/jobstates?limit=2&offset=2').data
    assert len(js['jobstates']) == 2

    # if offset is out of bound, the api returns an empty list
    js = user.get('/api/v1/jobstates?limit=5&offset=300')
    assert js.status_code == 200
    assert js.data['jobstates'] == []


def test_get_all_jobstates_with_embed(user, job_user_id, team_user_id):
    # create 2 jobstates and check meta data count
    data = {'job_id': job_user_id, 'status': 'running', 'comment': 'kikoolol1'}
    user.post('/api/v1/jobstates', data=data)
    js = user.post('/api/v1/jobstates', data=data).data

    t_utils.post_file(user, js['jobstate']['id'],
                      files.FileDesc('foo', 'bar'))

    data = {'job_id': job_user_id, 'status': 'running', 'comment': 'kikoolol2'}
    user.post('/api/v1/jobstates', data=data)

    # verify embed
    js = user.get('/api/v1/jobstates?embed=team,files&sort=created_at').data
    js_1 = js['jobstates'][0]
    js_2 = js['jobstates'][1]

    assert 'team' in js_1
    assert js_1['team']['id'] == team_user_id
    assert len(js_1['files']) == 0

    assert 'team' in js_2
    assert js_2['team']['id'] == team_user_id
    assert len(js_2['files']) == 1
    assert js_2['files'][0]['name'] == 'foo'


def test_get_all_jobstates_with_where(user, job_user_id):
    js = user.post('/api/v1/jobstates',
                   data={'job_id': job_user_id, 'status': 'running',
                         'comment': 'kikoolol'}).data
    js_id = js['jobstate']['id']

    db_js = user.get('/api/v1/jobstates?where=id:%s' % js_id).data
    db_js_id = db_js['jobstates'][0]['id']
    assert db_js_id == js_id

    db_js = user.get('/api/v1/jobstates?where=comment:kikoolol').data
    db_js_id = db_js['jobstates'][0]['id']
    assert db_js_id == js_id


def test_where_invalid(user):
    err = user.get('/api/v1/jobstates?where=id')

    assert err.status_code == 400
    assert err.data == {
        'status_code': 400,
        'message': 'Invalid where key: "id"',
        'payload': {
            'error': 'where key must have the following form "key:value"'
        }
    }


def test_get_all_jobstates_with_sort(user, job_user_id):
    # create 4 jobstates ordered by created time
    jd_1_1 = user.post('/api/v1/jobstates',
                       data={'job_id': job_user_id,
                             'status': 'running',
                             'comment': 'a'}).data['jobstate']
    jd_1_2 = user.post('/api/v1/jobstates',
                       data={'job_id': job_user_id,
                             'status': 'running',
                             'comment': 'a'}).data['jobstate']
    jd_2_1 = user.post('/api/v1/jobstates',
                       data={'job_id': job_user_id,
                             'status': 'running',
                             'comment': 'b'}).data['jobstate']
    jd_2_2 = user.post('/api/v1/jobstates',
                       data={'job_id': job_user_id,
                             'status': 'running',
                             'comment': 'b'}).data['jobstate']

    jds = user.get('/api/v1/jobstates?sort=created_at').data
    assert jds['jobstates'] == [jd_1_1, jd_1_2, jd_2_1, jd_2_2]

    # sort by comment first and then reverse by created_at
    jds = user.get('/api/v1/jobstates?sort=comment,-created_at').data
    assert jds['jobstates'] == [jd_1_2, jd_1_1, jd_2_2, jd_2_1]


def test_get_all_jobstates_with_sub_sort(user, job_user_id):
    # create 4 jobstates ordered by created time
    jd_1_1 = user.post('/api/v1/jobstates',
                       data={'job_id': job_user_id,
                             'status': 'running',
                             'comment': 'b'}).data['jobstate']
    jd_1_2 = user.post('/api/v1/jobstates',
                       data={'job_id': job_user_id,
                             'status': 'running',
                             'comment': 'a'}).data['jobstate']
    t_utils.post_file(user, jd_1_1['id'], files.FileDesc('foo', 'bar'))
    t_utils.post_file(user, jd_1_2['id'], files.FileDesc('older', 'bar'))
    t_utils.post_file(user, jd_1_2['id'], files.FileDesc('something', 'bar'))
    t_utils.post_file(user, jd_1_2['id'], files.FileDesc('latest', 'bar'))

    jds = user.get('/api/v1/jobstates?sort=comment' +
                   '&embed=files').data
    # check the sort by comment
    commands = [j['comment'] for j in jds['jobstates']]
    assert ['a', 'b'] == commands
    # check the order by file creation date
    names = [f['name'] for f in jds['jobstates'][0]['files']]
    # We don't preserve order of embedded resources
    assert {'latest', 'something', 'older'} == set(names)


def test_get_jobstate_by_id(user, job_user_id):
    js = user.post('/api/v1/jobstates',
                   data={'job_id': job_user_id,
                         'comment': 'kikoolol',
                         'status': 'running'}).data
    js_id = js['jobstate']['id']

    # get by uuid
    created_js = user.get('/api/v1/jobstates/%s' % js_id)
    assert created_js.status_code == 200
    assert created_js.data['jobstate']['comment'] == 'kikoolol'
    assert created_js.data['jobstate']['status'] == 'running'


def test_get_jobstate_not_found(user):
    result = user.get('/api/v1/jobstates/%s' % uuid.uuid4())
    assert result.status_code == 404


def test_get_jobstate_with_embed(user, job_user_id, team_user_id):
    pt = user.get('/api/v1/teams/%s' % team_user_id).data
    js = user.post('/api/v1/jobstates',
                   data={'job_id': job_user_id,
                         'comment': 'kikoolol',
                         'status': 'running'}).data
    js_id = js['jobstate']['id']
    js['jobstate'][u'team'] = pt['team']

    # verify embed
    js_embed = user.get('/api/v1/jobstates/%s?embed=team' % js_id).data
    assert js == js_embed


def test_get_jobstate_with_embed_not_valid(user, job_user_id):
    js = user.post('/api/v1/jobstates',
                   data={'job_id': job_user_id,
                         'comment': 'kikoolol',
                         'status': 'running'}).data
    js = user.get('/api/v1/jobstates/%s?embed=mdr' % js['jobstate']['id'])
    assert js.status_code == 400


def test_delete_jobstate_by_id(user, job_user_id):
    js = user.post('/api/v1/jobstates',
                   data={'job_id': job_user_id,
                         'comment': 'kikoolol',
                         'status': 'running'})
    js_id = js.data['jobstate']['id']

    url = '/api/v1/jobstates/%s' % js_id

    created_js = user.get(url)
    assert created_js.status_code == 200

    deleted_js = user.delete(url)
    assert deleted_js.status_code == 204

    gjs = user.get(url)
    assert gjs.status_code == 404

# Tests for the isolation


def test_create_jobstate_as_user(user, team_user_id, job_user_id):
    jobstate = user.post('/api/v1/jobstates',
                         data={'job_id': job_user_id,
                               'comment': 'kikoolol',
                               'status': 'running'})
    assert jobstate.status_code == 201

    jobstate_id = jobstate.data['jobstate']['id']
    jobstate = user.get('/api/v1/jobstates/%s' % jobstate_id)
    assert jobstate.data['jobstate']['team_id'] == team_user_id


def test_get_all_jobstates_as_user(user, team_user_id, jobstate_user_id):
    jobstates = user.get('/api/v1/jobstates')
    assert jobstates.status_code == 200
    assert jobstates.data['_meta']['count'] == 1
    for jobstate in jobstates.data['jobstates']:
        assert jobstate['team_id'] == team_user_id


def test_get_all_jobstates_as_product_owner(product_owner, team_user_id,
                                            jobstate_user_id):
    jobstates = product_owner.get('/api/v1/jobstates')
    assert jobstates.status_code == 200
    assert jobstates.data['_meta']['count'] == 1
    for jobstate in jobstates.data['jobstates']:
        assert jobstate['team_id'] == team_user_id


def test_get_jobstate_as_user(user, jobstate_user_id, job_user_id):
    # jobstate = user.get('/api/v1/jobstates/%s' % jobstate_id)
    # assert jobstate.status_code == 404

    jobstate = user.post('/api/v1/jobstates',
                         data={'job_id': job_user_id,
                               'comment': 'kikoolol',
                               'status': 'running'}).data
    jobstate_id = jobstate['jobstate']['id']
    jobstate = user.get('/api/v1/jobstates/%s' % jobstate_id)
    assert jobstate.status_code == 200


def test_delete_jobstate_as_user(user, job_user_id):
    js_user = user.post('/api/v1/jobstates',
                        data={'job_id': job_user_id,
                              'comment': 'kikoolol',
                              'status': 'running'})
    js_user_id = js_user.data['jobstate']['id']

    jobstate_delete = user.delete('/api/v1/jobstates/%s' % js_user_id)
    assert jobstate_delete.status_code == 204

    # jobstate_delete = user.delete('/api/v1/jobstates/%s' % jobstate_id)
    # assert jobstate_delete.status_code == 401
