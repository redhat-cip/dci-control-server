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


def topic_creation(identity, product):
    data = {'name': 'tname', 'product_id': product['id'],
            'component_types': ['type1', 'type2']}
    pt = identity.post('/api/v1/topics', data=data).data
    pt_id = pt['topic']['id']
    return identity.get('/api/v1/topics/%s' % pt_id)


def topic_creation_with_opts(identity, product):
    data = {'name': 'tname', 'product_id': product['id'],
            'component_types': ['type1', 'type2'],
            'data': {'foo': 'bar'}, 'label': 'rob'}
    pt = identity.post('/api/v1/topics', data=data).data
    pt_id = pt['topic']['id']
    t = identity.get('/api/v1/topics/%s' % pt_id)
    assert t['topic']['data']['foo'] == 'bar'
    assert t['topic']['label'] == 'rob'


def topic_update(identity, topic_id):
    t = identity.get('/api/v1/topics/' + topic_id).data['topic']
    data = {'component_types': ['lol1', 'lol2'],
            'data': {'foo': 'bar'}}
    identity.put('/api/v1/topics/' + topic_id, data=data,
                 headers={'If-match': t['etag']})

    return identity.get('/api/v1/topics/' + topic_id)


def topic_removal(identity, topic_id):
    return identity.delete('/api/v1/topics/%s' % topic_id)


def test_create_topics(admin, product):
    topic = topic_creation(admin, product).data
    assert topic['topic']['name'] == 'tname'
    assert topic['topic']['component_types'] == ['type1', 'type2']


def test_create_topic_as_feeder(feeder_context, product):
    topic = topic_creation(feeder_context, product).data
    assert topic['topic']['name'] == 'tname'
    assert topic['topic']['component_types'] == ['type1', 'type2']


def test_create_topics_as_user(user, product):
    data = {'name': 'tname', 'product_id': product['id'],
            'component_types': ['type1', 'type2']}
    status_code = user.post('/api/v1/topics', data=data).status_code
    assert status_code == 401


def test_update_topics_as_admin(admin, topic_id):
    topic = topic_update(admin, topic_id).data['topic']
    assert topic['component_types'] == ['lol1', 'lol2']
    assert topic['data']['foo'] == 'bar'


def test_update_topic_as_feeder(feeder_context, topic_id):
    topic = topic_update(feeder_context, topic_id).data['topic']
    assert topic['component_types'] == ['lol1', 'lol2']
    assert topic['data']['foo'] == 'bar'


def test_change_topic_state(admin, topic_id):
    t = admin.get('/api/v1/topics/' + topic_id).data['topic']
    data = {'state': 'inactive'}
    r = admin.put('/api/v1/topics/' + topic_id,
                  data=data,
                  headers={'If-match': t['etag']})
    assert r.status_code == 200
    assert r.data['topic']['state'] == 'inactive'


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


def test_create_topics_already_exist(admin, product):
    data = {'name': 'tname', 'product_id': product['id'],
            'component_types': ['type1', 'type2']}
    pstatus_code = admin.post('/api/v1/topics', data=data).status_code
    assert pstatus_code == 201

    data = {'name': 'tname', 'product_id': product['id'],
            'component_types': ['type1', 'type2']}
    pstatus_code = admin.post('/api/v1/topics', data=data).status_code
    assert pstatus_code == 409


def test_get_all_topics_by_admin(admin, product):
    created_topics_ids = []
    for i in range(5):
        pc = admin.post('/api/v1/topics',
                        data={'name': 'tname%s' % uuid.uuid4(),
                              'product_id': product['id'],
                              'component_types': ['type1', 'type2']}).data
        created_topics_ids.append(pc['topic']['id'])
    created_topics_ids.sort()

    db_all_cs = admin.get('/api/v1/topics').data
    db_all_cs = db_all_cs['topics']
    db_all_cs_ids = [db_ct['id'] for db_ct in db_all_cs]
    db_all_cs_ids.sort()

    assert db_all_cs_ids == created_topics_ids


def test_get_all_topics_by_user_and_remoteci(admin, user, remoteci_context,
                                             team_user_id, product):
    def test(caller, topic_name):
        # create a topic with export_control==False
        my_topic = admin.post('/api/v1/topics',
                              data={'name': topic_name,
                                    'product_id': product['id'],
                                    'export_control': False,
                                    'component_types': ['type1', 'type2']})
        assert my_topic.status_code == 201
        my_topic_id = my_topic.data['topic']['id']
        my_topic_etag = my_topic.data['topic']['etag']
        # user should not find it
        my_topic = caller.get('/api/v1/topics?where=name:%s' % topic_name)
        assert len(my_topic.data['topics']) == 0

        # associate the user's team to the topic
        pt = admin.post('/api/v1/topics/%s/teams' % my_topic_id,
                        data={'team_id': team_user_id})

        # user should see the topic now
        my_topic = caller.get('/api/v1/topics?where=name:%s' % topic_name)
        assert my_topic.data['topics'][0]['name'] == topic_name

        # remove user'team from topic
        pt = admin.delete('/api/v1/topics/%s/teams/%s' % (my_topic_id, team_user_id))  # noqa

        # user should not find it
        my_topic = caller.get('/api/v1/topics?where=name:%s' % topic_name)
        assert len(my_topic.data['topics']) == 0

        # update export_control to True
        admin.put('/api/v1/topics/%s' % my_topic_id,
                  headers={'If-match': my_topic_etag},
                  data={'export_control': True})

        # user should see the topic now
        my_topic = caller.get('/api/v1/topics?where=name:%s' % topic_name)
        assert my_topic.data['topics'][0]['name'] == topic_name
    test(user, 'my_new_topic_1')
    test(remoteci_context, 'my_new_topic_2')


def test_get_all_topics_with_pagination(admin, product):
    # create 20 topic types and check meta data count
    for i in range(20):
        admin.post('/api/v1/topics',
                   data={'name': 'tname%s' % uuid.uuid4(),
                         'product_id': product['id'],
                         'component_types': ['type1', 'type2']})
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


def test_get_all_topics_with_where(admin, product):
    # create 20 topic types and check meta data count
    topics = {}
    for i in range(20):
        t_name = str(uuid.uuid4())
        r = admin.post('/api/v1/topics',
                       data={'name': t_name,
                             'product_id': product['id'],
                             'component_types': ['type1', 'type2']}).data
        topics[t_name] = r['topic']['id']

    for t_name, t_id in topics.items():
        r = admin.get('/api/v1/topics?where=name:%s&limit=1&offset=0' % t_name).data
        assert r['_meta']['count'] == 1
        assert r['topics'][0]['id'] == t_id


def test_get_topics_of_user(admin, user, team_user_id, product):
    data = {'name': 'test_name', 'product_id': product['id'],
            'component_types': ['type1', 'type2']}
    topic = admin.post('/api/v1/topics', data=data).data['topic']
    topic_id = topic['id']
    admin.post('/api/v1/topics/%s/teams' % topic_id,
               data={'team_id': team_user_id})
    for i in range(5):
        admin.post('/api/v1/topics',
                   data={'name': 'tname%s' % uuid.uuid4(),
                         'product_id': product['id'],
                         'component_types': ['type1', 'type2'],
                         'data': {}})
    topics_user = user.get('/api/v1/topics').data
    assert topic == topics_user['topics'][0]
    assert len(topics_user['topics']) == 1


def test_get_topics_by_with_embed_authorization(admin, user, epm):
    topics_admin = admin.get('/api/v1/topics?embed=teams')
    assert topics_admin.status_code == 200

    topics_epm = admin.get('/api/v1/topics?embed=teams')
    assert topics_epm.status_code == 200

    topics_user = user.get('/api/v1/topics?embed=teams')
    assert topics_user.status_code == 401


def test_get_topic_by_id(admin, user, team_user_id, product):
    data = {'name': 'tname',
            'product_id': product['id'],
            'component_types': ['type1', 'type2']}
    pt = admin.post('/api/v1/topics', data=data).data
    pt_id = pt['topic']['id']

    admin.post('/api/v1/topics/%s/teams' % pt_id,
               data={'team_id': team_user_id})

    # get by uuid
    created_ct = user.get('/api/v1/topics/%s' % pt_id)
    assert created_ct.status_code == 200

    created_ct = created_ct.data
    assert created_ct['topic']['id'] == pt_id


def test_get_topic_by_id_with_embed_authorization(admin, user, topic_user_id):
    topics_admin = admin.get('/api/v1/topics/%s?embed=teams' % topic_user_id)
    assert topics_admin.status_code == 200

    topics_user = user.get('/api/v1/topics/%s?embed=teams' % topic_user_id)
    assert topics_user.status_code == 401


def test_get_topic_not_found(admin):
    result = admin.get('/api/v1/topics/%s' % uuid.uuid4())
    assert result.status_code == 404


def test_delete_topic_by_id(admin, topic_id):
    topic = topic_removal(admin, topic_id)
    assert topic.status_code == 204

    gct = admin.get('/api/v1/topics/%s' % topic_id)
    assert gct.status_code == 404


def test_delete_topic_by_id_as_user(admin, user, product):
    data = {'name': 'tname', 'product_id': product['id'],
            'component_types': ['type1', 'type2']}
    pt = admin.post('/api/v1/topics', data=data)
    pt_id = pt.data['topic']['id']
    assert pt.status_code == 201

    created_ct = admin.get('/api/v1/topics/%s' % pt_id)
    assert created_ct.status_code == 200

    deleted_ct = user.delete('/api/v1/topics/%s' % pt_id)
    assert deleted_ct.status_code == 401


def test_delete_topic_archive_dependencies(admin, product):
    topic = admin.post('/api/v1/topics',
                       data={'name': 'topic_name', 'product_id': product['id'],
                             'component_types': ['type1', 'type2']})
    topic_id = topic.data['topic']['id']
    assert topic.status_code == 201

    data = {
        'name': 'pname',
        'type': 'gerrit_review',
        'url': 'http://example.com/',
        'topic_id': topic_id,
        'state': 'active'}
    component = admin.post('/api/v1/components', data=data)
    component_id = component.data['component']['id']
    assert component.status_code == 201

    url = '/api/v1/topics/%s' % topic_id
    deleted_topic = admin.delete(url)
    assert deleted_topic.status_code == 204

    deleted_component = admin.get('/api/v1/component/%s' % component_id)
    assert deleted_component.status_code == 404


def test_purge_topic(admin, product):
    data = {'name': 'tname', 'product_id': product['id'],
            'component_types': ['type1', 'type2']}
    pt = admin.post('/api/v1/topics', data=data)
    pt_id = pt.data['topic']['id']
    assert pt.status_code == 201

    ppt = admin.delete('/api/v1/topics/%s' % pt_id)
    assert ppt.status_code == 204


def test_get_all_topics_sorted(admin, product):
    t1 = {'name': "c", 'product_id': product['id'], 'component_types': ['ct1']}
    tid_1 = admin.post('/api/v1/topics', data=t1).data['topic']['id']
    t2 = {'name': "b", 'product_id': product['id'], 'component_types': ['ct1']}
    tid_2 = admin.post('/api/v1/topics', data=t2).data['topic']['id']
    t3 = {'name': "a", 'product_id': product['id'], 'component_types': ['ct1']}
    tid_3 = admin.post('/api/v1/topics', data=t3).data['topic']['id']

    def get_ids(path):
        return [i['id'] for i in admin.get(path).data['topics']]

    assert get_ids('/api/v1/topics') == [tid_3, tid_2, tid_1]
    assert get_ids('/api/v1/topics?sort=created_at') == [tid_1, tid_2, tid_3]
    assert get_ids('/api/v1/topics?sort=-created_at') == [tid_3, tid_2, tid_1]
    assert get_ids('/api/v1/topics?sort=name') == [tid_3, tid_2, tid_1]


def test_delete_topic_not_found(admin):
    result = admin.delete('/api/v1/topics/%s' % uuid.uuid4())
    assert result.status_code == 404


def test_put_topics(admin, topic_id, product):
    pt = admin.post('/api/v1/topics',
                    data={'name': 'pname', 'product_id': product['id'],
                          'component_types': ['type1', 'type2']})
    assert pt.status_code == 201

    pt_etag = pt.headers.get("ETag")

    gt = admin.get('/api/v1/topics/%s' % pt.data['topic']['id'])
    assert gt.status_code == 200

    ppt = admin.put('/api/v1/topics/%s' % pt.data['topic']['id'],
                    data={'name': 'nname',
                          'next_topic_id': topic_id},
                    headers={'If-match': pt_etag})
    assert ppt.status_code == 200

    gt = admin.get('/api/v1/topics/%s?embed=next_topic' %
                   pt.data['topic']['id'])
    assert gt.status_code == 200
    assert gt.data['topic']['name'] == 'nname'
    assert gt.data['topic']['next_topic']['name'] == 'topic_name'


# Tests for topics and teams management
def test_add_team_to_topic_and_get(admin, product):
    # create a topic
    data = {'name': 'tname', 'product_id': product['id'],
            'component_types': ['type1', 'type2']}
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
    team_from_topic = admin.get(url)
    assert team_from_topic.status_code == 200
    assert team_from_topic.data['_meta']['count'] == 1
    assert team_from_topic.data['teams'][0] == pc['team']


# Tests for topics and teams management
def test_add_team_to_topic_and_get_as_user(admin, user, product):
    # create a topic
    data = {'name': 'tname', 'product_id': product['id'],
            'component_types': ['type1', 'type2']}
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


def test_delete_team_from_topic(admin, product):
    # create a topic
    data = {'name': 'tname', 'product_id': product['id'],
            'component_types': ['type1', 'type2']}
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


def test_delete_team_from_topic_as_user(admin, user, product):
    # create a topic
    data = {'name': 'tname', 'product_id': product['id'],
            'component_types': ['type1', 'type2']}
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


def test_remove_next_topic_from_topic(admin, topic_id, product):
    request = admin.post('/api/v1/topics',
                         data={'name': 'topic 1', 'next_topic_id': topic_id,
                               'product_id': product['id']})
    assert request.status_code == 201
    new_topic_id = request.data['topic']['id']

    t = admin.get('/api/v1/topics/%s' % new_topic_id).data['topic']
    assert t['next_topic_id'] == topic_id

    request2 = admin.put('/api/v1/topics/%s' % new_topic_id,
                         data={'next_topic_id': None},
                         headers={'If-match': request.headers.get("ETag")})
    assert request2.status_code == 200

    t = admin.get('/api/v1/topics/%s' % new_topic_id).data['topic']
    assert t['next_topic_id'] is None

    request3 = admin.put('/api/v1/topics/%s' % new_topic_id,
                         data={'next_topic_id': topic_id},
                         headers={'If-match': request2.headers.get("ETag")})
    assert request3.status_code == 200

    t = admin.get('/api/v1/topics/%s' % new_topic_id).data['topic']
    assert t['next_topic_id'] == topic_id


def test_component_success_update_field_by_field(admin, topic_id):
    t = admin.get('/api/v1/topics/%s' % topic_id).data['topic']

    admin.put('/api/v1/topics/%s' % topic_id,
              data={'state': 'inactive'},
              headers={'If-match': t['etag']})

    t = admin.get('/api/v1/topics/%s' % topic_id).data['topic']

    assert t['name'] == 'topic_name'
    assert t['state'] == 'inactive'

    admin.put('/api/v1/topics/%s' % topic_id,
              data={'name': 'topic_name2'},
              headers={'If-match': t['etag']})

    t = admin.get('/api/v1/topics/%s' % t['id']).data['topic']

    assert t['name'] == 'topic_name2'
    assert t['state'] == 'inactive'


def test_success_get_topics_embed(admin, topic_id, product_id):
    result = admin.get('/api/v1/topics/%s/?embed=product' % topic_id)

    assert result.status_code == 200
    assert 'product' in result.data['topic'].keys()

    request = admin.post('/api/v1/topics',
                         data={'name': 'topic_without_product',
                               'product_id': product_id})

    result = admin.get('/api/v1/topics')
    assert request.data['topic'] == result.data['topics'][0]


def test_add_multiple_topic_and_get(admin, user, product, product2):
    # create a topic from product
    data = {'name': 'tname', 'product_id': product['id'],
            'component_types': ['type1', 'type2']}
    pt = admin.post('/api/v1/topics', data=data).data
    pt_id = pt['topic']['id']

    # create a topic from product2
    data2 = {'name': 'tname2', 'product_id': product2['id'],
             'component_types': ['type1', 'type2']}
    pt2 = admin.post('/api/v1/topics', data=data2).data
    pt2_id = pt2['topic']['id']

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

    url = '/api/v1/topics/%s/teams' % pt2_id
    # add team to topic2
    data = {'team_id': team_id}
    res = admin.post(url, data=data)
    assert res.status_code == 201
    add_data = res.data
    assert add_data['topic_id'] == pt2_id
    assert add_data['team_id'] == team_id


def test_get_topic_by_id_export_control_true(
    admin, user, team_user_id, RHELProduct, RHEL80Topic
):
    request = admin.post(
        "/api/v1/products/%s/teams" % RHELProduct["id"], data={"team_id": team_user_id}
    )
    assert request.status_code == 201
    request = user.get("/api/v1/topics/%s" % RHEL80Topic["id"])
    assert request.status_code == 200
    assert request.data["topic"]["id"] == RHEL80Topic["id"]
