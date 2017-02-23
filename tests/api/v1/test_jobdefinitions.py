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
import uuid


def test_create_jobdefinitions(admin, topic_id):
    jd = admin.post('/api/v1/jobdefinitions',
                    data={'name': 'pname', 'topic_id': topic_id}).data
    jd_id = jd['jobdefinition']['id']
    jd = admin.get('/api/v1/jobdefinitions/%s' % jd_id).data
    assert jd['jobdefinition']['name'] == 'pname'


def test_get_all_jobdefinitions(jobdefinition_id, jobdefinition_user_id,
                                admin, user):
    res = admin.get('/api/v1/jobdefinitions')
    assert res.data['_meta']['count'] == 2
    assert len(res.data['jobdefinitions']) == 2

    res = user.get('/api/v1/jobdefinitions')
    assert res.data['_meta']['count'] == 1
    assert len(res.data['jobdefinitions']) == 1


def test_get_all_jobdefinitions_with_id(admin, topic_id):
    data = {'name': 'pname1', 'topic_id': topic_id}
    jd_1 = admin.post('/api/v1/jobdefinitions', data=data).data
    jd_1_id = jd_1['jobdefinition']['id']

    data = {'name': 'pname2', 'topic_id': topic_id}
    jd_2 = admin.post('/api/v1/jobdefinitions', data=data).data
    jd_2_id = jd_2['jobdefinition']['id']

    db_all_jds = admin.get(
        '/api/v1/topics/%s/jobdefinitions?sort=created_at' % topic_id).data
    db_all_jds = db_all_jds['jobdefinitions']
    db_all_jds_ids = [db_jd['id'] for db_jd in db_all_jds]

    assert db_all_jds_ids == [jd_1_id, jd_2_id]


def test_get_all_jobdefinitions_not_in_topic(admin, user):
    topic = admin.post('/api/v1/topics', data={'name': 'topic_test'}).data
    topic_id = topic['topic']['id']
    status_code = user.get(
        '/api/v1/topics/%s/jobdefinitions' % topic_id).status_code
    assert status_code == 412


def test_get_all_jobdefinitions_with_pagination(admin, topic_id):
    # create 4 jobdefinition types and check meta count
    data = {'name': 'pname1', 'topic_id': topic_id}
    admin.post('/api/v1/jobdefinitions', data=data)
    data = {'name': 'pname2', 'topic_id': topic_id}
    admin.post('/api/v1/jobdefinitions', data=data)
    data = {'name': 'pname3', 'topic_id': topic_id}
    admin.post('/api/v1/jobdefinitions', data=data)
    data = {'name': 'pname4', 'topic_id': topic_id}
    admin.post('/api/v1/jobdefinitions', data=data)

    # check meta count
    jds = admin.get('/api/v1/topics/%s/jobdefinitions' % topic_id).data
    assert jds['_meta']['count'] == 4

    # verify limit and offset are working well
    jds = admin.get(
        '/api/v1/topics/%s/jobdefinitions?limit=2&offset=0' % topic_id).data
    assert len(jds['jobdefinitions']) == 2

    jds = admin.get(
        '/api/v1/topics/%s/jobdefinitions?limit=2&offset=2' % topic_id).data
    assert len(jds['jobdefinitions']) == 2

    # if offset is out of bound, the api returns an empty list
    jds = admin.get(
        '/api/v1/topics/%s/jobdefinitions?limit=5&offset=300' % topic_id)
    assert jds.status_code == 200
    assert jds.data['jobdefinitions'] == []


def test_get_all_jobdefinitions_with_where(admin, topic_id):
    data = {'name': 'pname1', 'topic_id': topic_id}
    pjd = admin.post('/api/v1/jobdefinitions', data=data).data
    pjd_id = pjd['jobdefinition']['id']

    db_jd = admin.get(
        '/api/v1/topics/%s/jobdefinitions?where=id:%s' %
        (topic_id, pjd_id)).data
    db_jd_id = db_jd['jobdefinitions'][0]['id']
    assert db_jd_id == pjd_id

    db_jd = admin.get(
        '/api/v1/topics/%s/jobdefinitions?where=name:pname1' % topic_id).data
    db_jd_id = db_jd['jobdefinitions'][0]['id']
    assert db_jd_id == pjd_id


def test_get_all_jobdefinitions_with_embed(jobdefinition_id,
                                           admin):
    res = admin.get('/api/v1/jobdefinitions?embed=topic')
    assert res.data['jobdefinitions'][0]['topic']['name'] == 'topic_name'


def test_where_invalid(admin, topic_id):
    err = admin.get('/api/v1/topics/%s/jobdefinitions?where=id' % topic_id)

    assert err.status_code == 400
    assert err.data == {
        'status_code': 400,
        'message': 'Invalid where key: "id"',
        'payload': {
            'error': 'where key must have the following form "key:value"'
        }
    }


def test_get_jobdefinition_by_id(admin, topic_id):
    pjd = admin.post('/api/v1/jobdefinitions',
                     data={'name': 'pname', 'topic_id': topic_id}).data
    pjd_id = pjd['jobdefinition']['id']

    # get by uuid
    created_ct = admin.get('/api/v1/jobdefinitions/%s' % pjd_id)
    assert created_ct.status_code == 200

    created_ct = created_ct.data
    assert created_ct['jobdefinition']['id'] == pjd_id


def test_get_all_jobdefinition_by_id_with_embed(jobdefinition_id,
                                                admin):
    res = admin.get('/api/v1/jobdefinitions/%s?embed=topic' % jobdefinition_id)
    assert res.data['jobdefinition']['topic']['name'] == 'topic_name'


def test_get_jobdefinition_not_found(admin):
    result = admin.get('/api/v1/jobdefinitions/ptdr')
    assert result.status_code == 404


def test_put_jobdefinitions(admin, topic_id):
    jd = admin.post('/api/v1/jobdefinitions',
                    data={'name': 'pname', 'topic_id': topic_id}).data
    jd_id = jd['jobdefinition']['id']
    jd = admin.get('/api/v1/jobdefinitions/%s' % jd_id).data
    jd_etag = jd['jobdefinition']['etag']
    assert jd['jobdefinition']['name'] == 'pname'

    # Update the 'active' field
    #
    ppt = admin.put('/api/v1/jobdefinitions/%s' % jd_id,
                    data={'state': 'inactive'}, headers={'If-match': jd_etag})
    assert ppt.status_code == 204

    gt = admin.get('/api/v1/jobdefinitions/%s' % jd_id).data
    gt_etag = gt['jobdefinition']['etag']
    assert gt['jobdefinition']['name'] == 'pname'
    assert gt['jobdefinition']['state'] == 'inactive'

    # Update the 'comment' field
    #
    ppt = admin.put('/api/v1/jobdefinitions/%s' % jd_id,
                    data={'comment': 'A comment'},
                    headers={'If-match': gt_etag})
    assert ppt.status_code == 204

    gt = admin.get('/api/v1/jobdefinitions/%s' % jd_id).data
    gt_etag = gt['jobdefinition']['etag']
    assert gt['jobdefinition']['name'] == 'pname'
    assert gt['jobdefinition']['state'] == 'inactive'
    assert gt['jobdefinition']['comment'] == 'A comment'

    # Update the 'priority' field
    #
    ppt = admin.put('/api/v1/jobdefinitions/%s' % jd_id,
                    data={'priority': 10}, headers={'If-match': gt_etag})
    assert ppt.status_code == 204
    gt = admin.get('/api/v1/jobdefinitions/%s' % jd_id).data
    gt_etag = gt['jobdefinition']['etag']
    assert gt['jobdefinition']['name'] == 'pname'
    assert gt['jobdefinition']['priority'] == 10
    assert gt['jobdefinition']['comment'] == 'A comment'
    assert gt['jobdefinition']['state'] == 'inactive'

    # Update the 'name' field
    #
    ppt = admin.put('/api/v1/jobdefinitions/%s' % jd_id,
                    data={'name': 'newname'}, headers={'If-match': gt_etag})
    assert ppt.status_code == 204
    gt = admin.get('/api/v1/jobdefinitions/%s' % jd_id).data
    assert gt['jobdefinition']['name'] == 'newname'
    assert gt['jobdefinition']['priority'] == 10
    assert gt['jobdefinition']['comment'] == 'A comment'
    assert gt['jobdefinition']['state'] == 'inactive'


def test_delete_jobdefinition_by_id(admin, topic_id):
    data = {'name': 'pname', 'topic_id': topic_id}
    pjd = admin.post('/api/v1/jobdefinitions', data=data)
    pct_etag = pjd.headers.get("ETag")
    pjd_id = pjd.data['jobdefinition']['id']
    assert pjd.status_code == 201

    url = '/api/v1/jobdefinitions/%s' % pjd_id

    created_jd = admin.get(url)
    assert created_jd.status_code == 200

    deleted_jd = admin.delete(url, headers={'If-match': pct_etag})
    assert deleted_jd.status_code == 204

    gjd = admin.get('/api/v1/jobdefinitions/%s' % pjd_id)
    assert gjd.status_code == 404


def test_get_all_jobdefinitions_with_sort(admin, topic_id):
    # create 4 jobdefinitions ordered by created time
    jd_1_1 = admin.post('/api/v1/jobdefinitions',
                        data={'name': "pname1", 'priority': 0,
                              'topic_id': topic_id}).data['jobdefinition']
    jd_1_2 = admin.post('/api/v1/jobdefinitions',
                        data={'name': "pname2", 'priority': 0,
                              'topic_id': topic_id}).data['jobdefinition']
    jd_2_1 = admin.post('/api/v1/jobdefinitions',
                        data={'name': "pname3", 'priority': 1,
                              'topic_id': topic_id}).data['jobdefinition']
    jd_2_2 = admin.post('/api/v1/jobdefinitions',
                        data={'name': "pname4", 'priority': 1,
                              'topic_id': topic_id}).data['jobdefinition']

    jds = admin.get(
        '/api/v1/topics/%s/jobdefinitions?sort=created_at' % topic_id).data
    assert jds['jobdefinitions'] == [jd_1_1, jd_1_2, jd_2_1, jd_2_2]

    # sort by priority first and then reverse by created_at
    jds = admin.get(
        '/api/v1/topics/%s/jobdefinitions?sort=priority,-created_at' %
        topic_id).data
    assert jds['jobdefinitions'] == [jd_1_2, jd_1_1, jd_2_2, jd_2_1]


def test_delete_jobdefinition_not_found(admin):
    url = '/api/v1/jobdefinitions/%s' % uuid.uuid4()
    result = admin.delete(url, headers={'If-match': 'mdr'})
    assert result.status_code == 404


# Tests for jobdefinition and tests management
def test_add_test_to_jobdefinitions_and_get(admin, test_id, topic_id):
    # create a jobdefinition
    data = {'name': 'pname', 'topic_id': topic_id}
    pjd = admin.post('/api/v1/jobdefinitions', data=data).data
    pjd_id = pjd['jobdefinition']['id']

    # attach a test to jobdefinition
    url = '/api/v1/jobdefinitions/%s/tests' % pjd_id
    add_data = admin.post(url, data={'test_id': test_id}).data
    assert add_data['jobdefinition_id'] == pjd_id
    assert add_data['test_id'] == test_id

    # get test from jobdefinition
    test_from_jobdefinition = admin.get(url).data
    assert test_from_jobdefinition['_meta']['count'] == 1
    assert test_from_jobdefinition['tests'][0]['id'] == test_id


def test_delete_test_from_jobdefinition(admin, test_id, topic_id):
    # create a jobdefinition
    data = {'name': 'pname', 'topic_id': topic_id}
    pjd = admin.post('/api/v1/jobdefinitions', data=data).data
    pjd_id = pjd['jobdefinition']['id']

    # check that the jobdefinition a as test attached
    url = '/api/v1/jobdefinitions/%s/tests' % pjd_id
    admin.post(url, data={'test_id': test_id})
    test_from_jobdefinition = admin.get(
        '/api/v1/jobdefinitions/%s/tests' % pjd_id).data
    assert test_from_jobdefinition['_meta']['count'] == 1

    # unattach test from jobdefinition
    admin.delete('/api/v1/jobdefinitions/%s/tests/%s' % (pjd_id, test_id))
    test_from_jobdefinition = admin.get(url).data
    assert test_from_jobdefinition['_meta']['count'] == 0

    # verify test still exist on /tests
    c = admin.get('/api/v1/tests/%s' % test_id)
    assert c.status_code == 200


def test_change_jobdefinition_state(admin, jobdefinition_id):
    t = admin.get('/api/v1/jobdefinitions/' + jobdefinition_id)
    t = t.data['jobdefinition']
    data = {'state': 'inactive'}
    r = admin.put('/api/v1/jobdefinitions/' + jobdefinition_id,
                  data=data,
                  headers={'If-match': t['etag']})
    assert r.status_code == 204
    jd = admin.get('/api/v1/jobdefinitions/' + jobdefinition_id)
    jd = jd.data['jobdefinition']
    assert jd['state'] == 'inactive'


def test_change_jobdefinition_to_invalid_state(admin, jobdefinition_id):
    t = admin.get('/api/v1/jobdefinitions/' + jobdefinition_id)
    t = t.data['jobdefinition']
    data = {'state': 'kikoolol'}
    r = admin.put('/api/v1/jobdefinitions/' + jobdefinition_id,
                  data=data,
                  headers={'If-match': t['etag']})
    assert r.status_code == 400
    jd = admin.get('/api/v1/jobdefinitions/' + jobdefinition_id)
    assert jd.status_code == 200
    assert jd.data['jobdefinition']['state'] == 'active'
