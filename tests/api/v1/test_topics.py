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


def test_create_topics(admin):
    data = {'name': 'tname'}
    pt = admin.post('/api/v1/topics', data=data).data
    pt_id = pt['topic']['id']
    gc = admin.get('/api/v1/topics/%s' % pt_id).data
    assert gc['topic']['name'] == 'tname'


def test_create_topics_as_user(user):
    data = {'name': 'tname'}
    status_code = user.post('/api/v1/topics', data=data).status_code
    assert status_code == 401


def test_update_topics_as_admin(admin, topic_id):
    t = admin.get('/api/v1/topics/' + topic_id).data['topic']
    data = {'label': 'my comment'}
    r = admin.put('/api/v1/topics/' + topic_id,
                  data=data,
                  headers={'If-match': t['etag']})
    assert r.status_code == 204
    current_topic = admin.get('/api/v1/topics/' + topic_id).data['topic']
    assert current_topic['label'] == 'my comment'


def test_change_topic_state(admin, topic_id):
    t = admin.get('/api/v1/topics/' + topic_id).data['topic']
    data = {'state': 'inactive'}
    r = admin.put('/api/v1/topics/' + topic_id,
                  data=data,
                  headers={'If-match': t['etag']})
    assert r.status_code == 204
    current_topic = admin.get('/api/v1/topics/' + topic_id).data['topic']
    assert current_topic['state'] == 'inactive'


def test_change_topic_to_invalid_state(admin, topic_id):
    t = admin.get('/api/v1/topics/' + topic_id).data['topic']
    data = {'state': 'kikoolol'}
    r = admin.put('/api/v1/topics/' + topic_id,
                  data=data,
                  headers={'If-match': t['etag']})
    assert r.status_code == 400
    current_topic = admin.get('/api/v1/topics/' + topic_id)
    assert current_topic.status_code == 200
    assert current_topic.data['topic']['state'] == 'active'


def test_create_topics_already_exist(admin):
    data = {'name': 'tname'}
    pstatus_code = admin.post('/api/v1/topics', data=data).status_code
    assert pstatus_code == 201

    data = {'name': 'tname'}
    pstatus_code = admin.post('/api/v1/topics', data=data).status_code
    assert pstatus_code == 409


def test_get_all_topics_by_admin(admin):
    created_topics_ids = []
    for i in range(5):
        pc = admin.post('/api/v1/topics',
                        data={'name': 'tname%s' % uuid.uuid4()}).data
        created_topics_ids.append(pc['topic']['id'])
    created_topics_ids.sort()

    db_all_cs = admin.get('/api/v1/topics').data
    db_all_cs = db_all_cs['topics']
    db_all_cs_ids = [db_ct['id'] for db_ct in db_all_cs]
    db_all_cs_ids.sort()

    assert db_all_cs_ids == created_topics_ids


def test_get_all_topics_with_pagination(admin):
    # create 20 topic types and check meta data count
    for i in range(20):
        admin.post('/api/v1/topics',
                   data={'name': 'tname%s' % uuid.uuid4()})
    cs = admin.get('/api/v1/topics').data
    assert cs['_meta']['count'] == 20

    # verify limit and offset are working well
    for i in range(4):
        cs = admin.get(
            '/api/v1/topics?limit=5&offset=%s' % (i * 5)).data
        assert len(cs['topics']) == 5

    # if offset is out of bound, the api returns an empty list
    cs = admin.get('/api/v1/topics?limit=5&offset=300')
    assert cs.status_code == 200
    assert cs.data['topics'] == []


def test_get_all_topics_with_where(admin):
    # create 20 topic types and check meta data count
    topics = {}
    for i in range(20):
        t_name = str(uuid.uuid4())
        r = admin.post('/api/v1/topics',
                       data={'name': t_name}).data
        topics[t_name] = r['topic']['id']

    for t_name, t_id in topics.items():
        r = admin.get('/api/v1/topics?where=name:%s&limit=1' % t_name).data
        assert r['_meta']['count'] == 1
        assert r['topics'][0]['id'] == t_id


def test_get_topics_of_user(admin, user, team_user_id):
    data = {'name': 'test_name'}
    topic = admin.post('/api/v1/topics', data=data).data['topic']
    topic_id = topic['id']
    admin.post('/api/v1/topics/%s/teams' % topic_id,
               data={'team_id': team_user_id})
    for i in range(5):
        admin.post('/api/v1/topics',
                   data={'name': 'tname%s' % uuid.uuid4()})
    topics_user = user.get('/api/v1/topics').data
    assert topic == topics_user['topics'][0]
    assert len(topics_user['topics']) == 1


def test_get_topics_of_user_with_embed(admin, user, team_user_id):
    data = {'name': 'test_name'}
    topic = admin.post('/api/v1/topics', data=data).data['topic']
    topic_id = topic['id']
    admin.post('/api/v1/topics/%s/teams' % topic_id,
               data={'team_id': team_user_id})
    for i in range(5):
        admin.post('/api/v1/topics',
                   data={'name': 'tname%s' % uuid.uuid4()})
    topics_user = user.get('/api/v1/topics?embed=teams').data
    assert topics_user['topics'][0]['teams']
    assert len(topics_user['topics'][0]['teams']) > 0


def test_get_topic_by_id(admin, user, team_user_id):
    data = {'name': 'tname'}
    pt = admin.post('/api/v1/topics', data=data).data
    pt_id = pt['topic']['id']

    admin.post('/api/v1/topics/%s/teams' % pt_id,
               data={'team_id': team_user_id})

    # get by uuid
    created_ct = user.get('/api/v1/topics/%s' % pt_id)
    assert created_ct.status_code == 200

    created_ct = created_ct.data
    assert created_ct['topic']['id'] == pt_id


def test_get_topic_not_found(admin):
    result = admin.get('/api/v1/topics/%s' % uuid.uuid4())
    assert result.status_code == 404


def test_delete_topic_by_id(admin):
    data = {'name': 'tname'}
    pt = admin.post('/api/v1/topics', data=data)
    pt_id = pt.data['topic']['id']
    assert pt.status_code == 201

    created_ct = admin.get('/api/v1/topics/%s' % pt_id)
    assert created_ct.status_code == 200

    deleted_ct = admin.delete('/api/v1/topics/%s' % pt_id)
    assert deleted_ct.status_code == 204

    gct = admin.get('/api/v1/topics/%s' % pt_id)
    assert gct.status_code == 404


def test_delete_topic_by_id_as_user(admin, user):
    data = {'name': 'tname'}
    pt = admin.post('/api/v1/topics', data=data)
    pt_id = pt.data['topic']['id']
    assert pt.status_code == 201

    created_ct = admin.get('/api/v1/topics/%s' % pt_id)
    assert created_ct.status_code == 200

    deleted_ct = user.delete('/api/v1/topics/%s' % pt_id)
    assert deleted_ct.status_code == 401


def test_purge_topic(admin):
    data = {'name': 'tname'}
    pt = admin.post('/api/v1/topics', data=data)
    pt_id = pt.data['topic']['id']
    assert pt.status_code == 201

    ppt = admin.delete('/api/v1/topics/%s' % pt_id)
    assert ppt.status_code == 204


def test_get_all_topics_with_sort(admin):
    # create 4 topics ordered by created time
    data = {'name': "tname3", 'created_at': '2015-01-01'}
    ct_2_1 = admin.post('/api/v1/topics', data=data).data['topic']['id']
    data = {'name': "tname4", 'created_at': '2016-01-01'}
    ct_2_2 = admin.post('/api/v1/topics', data=data).data['topic']['id']
    data = {'name': "tname1", 'created_at': '2010-01-01'}
    ct_1_1 = admin.post('/api/v1/topics', data=data).data['topic']['id']
    data = {'name': "tname2", 'created_at': '2011-01-01'}
    ct_1_2 = admin.post('/api/v1/topics', data=data).data['topic']['id']

    def get_ids(path):
        return [i['id'] for i in admin.get(path).data['topics']]

    # default is to sort by name
    cts_ids = get_ids('/api/v1/topics')
    assert cts_ids == [ct_1_1, ct_1_2, ct_2_1, ct_2_2]

    cts_ids = get_ids('/api/v1/topics?sort=created_at')
    assert cts_ids == [ct_1_1, ct_1_2, ct_2_1, ct_2_2]

    # sort by title first and then reverse by created_at
    cts_ids = get_ids('/api/v1/topics?sort=-name')
    assert cts_ids == [ct_2_2, ct_2_1, ct_1_2, ct_1_1]


def test_delete_topic_not_found(admin):
    result = admin.delete('/api/v1/topics/%s' % uuid.uuid4())
    assert result.status_code == 404


def test_put_topics(admin, topic_id):
    pt = admin.post('/api/v1/topics', data={'name': 'pname'})
    assert pt.status_code == 201

    pt_etag = pt.headers.get("ETag")

    gt = admin.get('/api/v1/topics/%s' % pt.data['topic']['id'])
    assert gt.status_code == 200

    ppt = admin.put('/api/v1/topics/%s' % pt.data['topic']['id'],
                    data={'name': 'nname',
                          'next_topic': topic_id},
                    headers={'If-match': pt_etag})
    assert ppt.status_code == 204

    gt = admin.get('/api/v1/topics/%s' % pt.data['topic']['id'])
    assert gt.status_code == 200
    assert gt.data['topic']['name'] == 'nname'


# Tests for topics and teams management
def test_add_team_to_topic_and_get(admin):
    # create a topic
    data = {'name': 'tname'}
    pt = admin.post('/api/v1/topics', data=data).data
    pt_id = pt['topic']['id']

    # create a team
    data = {'name': 'tname1'}
    pc = admin.post('/api/v1/teams', data=data).data
    team_id = pc['team']['id']

    url = '/api/v1/topics/%s/teams' % pt_id
    # add team to topic
    data = {'team_id': team_id}
    res = admin.post(url, data=data)
    assert res.status_code == 201
    add_data = res.data
    assert add_data['topic_id'] == pt_id
    assert add_data['team_id'] == team_id

    # get teams from topic
    team_from_topic = admin.get(url).data
    assert team_from_topic['_meta']['count'] == 1
    assert team_from_topic['teams'][0] == pc['team']


# Tests for topics and teams management
def test_add_team_to_topic_and_get_as_user(admin, user):
    # create a topic
    data = {'name': 'tname'}
    pt = admin.post('/api/v1/topics', data=data).data
    pt_id = pt['topic']['id']

    # create a team
    data = {'name': 'tname1'}
    pc = admin.post('/api/v1/teams', data=data).data
    team_id = pc['team']['id']

    url = '/api/v1/topics/%s/teams' % pt_id
    # add team to topic
    data = {'team_id': team_id}
    status_code = user.post(url, data=data).status_code
    assert status_code == 401


def test_delete_team_from_topic(admin):
    # create a topic
    data = {'name': 'tname'}
    pt = admin.post('/api/v1/topics', data=data).data
    pt_id = pt['topic']['id']

    # create a team
    data = {'name': 'tname1'}
    pc = admin.post('/api/v1/teams', data=data).data
    team_id = pc['team']['id']

    url = '/api/v1/topics/%s/teams' % pt_id
    # add team to topic
    data = {'team_id': team_id}
    admin.post(url, data=data)

    # delete team from topic
    admin.delete('/api/v1/topics/%s/teams/%s' % (pt_id, team_id))
    team_from_topic = admin.get(url).data
    assert team_from_topic['_meta']['count'] == 0

    # verify team still exists on /teams
    c = admin.get('/api/v1/teams/%s' % team_id)
    assert c.status_code == 200


def test_delete_team_from_topic_as_user(admin, user):
    # create a topic
    data = {'name': 'tname'}
    pt = admin.post('/api/v1/topics', data=data).data
    pt_id = pt['topic']['id']

    # create a team
    data = {'name': 'tname1'}
    pc = admin.post('/api/v1/teams', data=data).data
    team_id = pc['team']['id']

    url = '/api/v1/topics/%s/teams' % pt_id
    # add team to topic
    data = {'team_id': team_id}
    admin.post(url, data=data)

    # delete team from topic
    status_code = user.delete(
        '/api/v1/topics/%s/teams/%s' % (pt_id, team_id)).status_code
    assert status_code == 401


def test_status_from_component_type_last_component(admin, topic_id,
                                                   components_ids,
                                                   remoteci_id,
                                                   jobdefinition_id, team_id):
    data = {
        'jobdefinition_id': jobdefinition_id,
        'team_id': team_id,
        'remoteci_id': remoteci_id,
        'components': components_ids
    }
    job = admin.post('/api/v1/jobs', data=data).data['job']
    data_update = {'status': 'success'}
    admin.put('/api/v1/jobs/%s' % job['id'], data=data_update,
              headers={'If-match': job['etag']})
    status = admin.get('/api/v1/topics/%s/type/type_1/status' % topic_id).data

    assert len(status['jobs']) == 1
    assert status['jobs'][0]['job_status'] == 'success'
    assert status['jobs'][0]['component_type'] == 'type_1'
    assert 'name-' in status['jobs'][0]['component_name']

    # Adding a new version of the component
    # so the query to topics/<t_id>/type/<type_id>/status
    # doesn't changes and retrieve previous job
    data = {
        'name': 'newversion',
        'type': 'type_1',
        'url': 'http://example.com/',
        'topic_id': topic_id,
        'export_control': True,
        'state': 'active'}
    admin.post('/api/v1/components', data=data).data

    status = admin.get('/api/v1/topics/%s/type/type_1/status' % topic_id).data

    assert len(status['jobs']) == 1
    assert status['jobs'][0]['job_status'] == 'success'
    assert status['jobs'][0]['component_type'] == 'type_1'
    assert 'name-' in status['jobs'][0]['component_name']


def test_status_from_component_type_get_status(admin, topic_id, components_ids,
                                               remoteci_id, jobdefinition_id,
                                               team_id):
    data = {
        'jobdefinition_id': jobdefinition_id,
        'team_id': team_id,
        'remoteci_id': remoteci_id,
        'components': components_ids,
    }
    job = admin.post('/api/v1/jobs', data=data).data['job']
    data_update = {'status': 'success'}
    admin.put('/api/v1/jobs/%s' % job['id'], data=data_update,
              headers={'If-match': job['etag']})
    status = admin.get('/api/v1/topics/%s/type/type_1/status' % topic_id).data

    assert len(status['jobs']) == 1
    assert status['jobs'][0]['job_status'] == 'success'
    assert status['jobs'][0]['component_type'] == 'type_1'
    assert 'name-' in status['jobs'][0]['component_name']

    job = admin.get('/api/v1/jobs/%s' % job['id']).data['job']
    data_update = {'status': 'killed'}
    admin.put('/api/v1/jobs/%s' % job['id'], data=data_update,
              headers={'If-match': job['etag']})
    status = admin.get('/api/v1/topics/%s/type/type_1/status' % topic_id).data

    assert len(status['jobs']) == 0

    job = admin.get('/api/v1/jobs/%s' % job['id']).data['job']
    data_update = {'status': 'failure'}
    admin.put('/api/v1/jobs/%s' % job['id'], data=data_update,
              headers={'If-match': job['etag']})
    status = admin.get('/api/v1/topics/%s/type/type_1/status' % topic_id).data

    assert len(status['jobs']) == 1
    assert status['jobs'][0]['job_status'] == 'failure'
    assert status['jobs'][0]['component_type'] == 'type_1'
    assert 'name-' in status['jobs'][0]['component_name']
