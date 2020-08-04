# -*- coding: utf-8 -*-
#
# Copyright (C) Red Hat, Inc
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

import uuid


def test_create_components(user, topic_id, team_user_id):
    data = {
        'name': 'my_tests',
        'type': 'ose-test',
        'url': 'http://exampletests.com/',
        'state': 'active',
        'tags': ['vanilla', 'core1']}
    pc = user.post('/api/v1/teams/%s/components' % team_user_id, data=data).data
    pc_id = pc['component']['id']
    gc = user.get('/api/v1/teams/%s/components/%s' % (team_user_id, pc_id)).data
    assert gc['component']['name'] == 'my_tests'
    assert gc['component']['state'] == 'active'


def test_get_all_components(user, team_user_id):
    created_c_ids = []
    for i in range(5):
        pc = user.post('/api/v1/teams/%s/components' % team_user_id,
                       data={'name': 'pname%s' % uuid.uuid4(),
                             'type': 'mytype',
                             'tags': ['edge']}).data
        created_c_ids.append(pc['component']['id'])
    created_c_ids.sort()

    db_all_cs = user.get('/api/v1/teams/%s/components' % team_user_id).data
    db_all_cs = db_all_cs['components']
    db_all_cs_ids = [db_ct['id'] for db_ct in db_all_cs]
    db_all_cs_ids.sort()

    assert db_all_cs_ids == created_c_ids


def test_get_component_by_id(user, team_user_id):
    data = {'name': 'pname',
            'type': 'gerrit_review'}
    pc = user.post('/api/v1/teams/%s/components' % team_user_id, data=data).data
    pc_id = pc['component']['id']

    # get by uuid
    created_ct = user.get('/api/v1/teams/%s/components/%s' % (team_user_id, pc_id))
    assert created_ct.status_code == 200

    created_ct = created_ct.data
    assert created_ct['component']['id'] == pc_id


def test_delete_component_by_id(user, team_user_id):

    data = {'name': 'pname',
            'type': 'mytest'
            }
    pc = user.post('/api/v1/teams/%s/components' % team_user_id, data=data).data
    pc_id = pc['component']['id']

    # get by uuid
    created_ct = user.get('/api/v1/teams/%s/components/%s' % (team_user_id, pc_id))
    assert created_ct.status_code == 200

    created_ct = created_ct.data
    assert created_ct['component']['id'] == pc_id

    deleted_ct = user.delete('/api/v1/teams/%s/components/%s' % (team_user_id, pc_id))
    assert deleted_ct.status_code == 204

    gct = user.get('/api/v1/teams/%s/components/%s' % (team_user_id, pc_id))
    assert gct.status_code == 404


def test_add_and_delete_tags_components(user, team_user_id):
    data = {'name': 'pname',
            'type': 'mytest'
            }
    pc = user.post('/api/v1/teams/%s/components' % team_user_id, data=data).data
    pc_id = pc['component']['id']

    pt = user.post('/api/v1/teams/%s/components/%s/tags' % (team_user_id, pc_id),
                   data={'name': 'my_tag_1'})
    assert pt.status_code == 201

    pt = user.post('/api/v1/teams/%s/components/%s/tags' % (team_user_id, pc_id),
                   data={'name': 'my_tag_1'})
    assert pt.status_code == 201

    pt = user.post('/api/v1/teams/%s/components/%s/tags' % (team_user_id, pc_id),
                   data={'name': 'my_tag_2'})
    assert pt.status_code == 201

    gt = user.get('/api/v1/teams/%s/components/%s' % (team_user_id, pc_id))
    assert gt.status_code == 200
    assert gt.data['component']['tags'] == ['my_tag_1', 'my_tag_2']

    dt = user.delete('/api/v1/teams/%s/components/%s/tags' % (team_user_id, pc_id),
                     data={'name': 'my_tag_2'})
    assert dt.status_code == 204

    gt = user.get('/api/v1/teams/%s/components/%s' % (team_user_id, pc_id))
    assert gt.status_code == 200
    assert gt.data['component']['tags'] == ['my_tag_1']


def test_filter_component_by_tag(user, team_user_id):

    data = {'name': 'pname',
            'type': 'mytest',
            'tags': ['tag1', 'common']}
    user.post('/api/v1/teams/%s/components' % team_user_id, data=data).data

    data = {'name': 'pname',
            'type': 'mylib',
            'tags': ['tag2', 'common']
            }
    user.post('/api/v1/teams/%s/components' % team_user_id, data=data).data

    res = user.get('/api/v1/teams/%s/components?where=tags:tag1' %
                   team_user_id)
    assert len(res.data['components']) == 1
    assert 'tag1' in res.data['components'][0]['tags']
    assert 'tag2' not in res.data['components'][0]['tags']

    res = user.get('/api/v1/teams/%s/components?where=tags:common' %
                   team_user_id)
    assert len(res.data['components']) == 2
    assert 'common' in res.data['components'][0]['tags']
    assert 'common' in res.data['components'][1]['tags']


def test_teams_components_isolation(user, user2, team_user_id):
    data = {'name': 'pname',
            'type': 'mytest'}
    user.post('/api/v1/teams/%s/components' % team_user_id, data=data).data
    components = user.get('/api/v1/teams/%s/components' % team_user_id).data
    assert len(components['components']) > 0
    components = user2.get('/api/v1/teams/%s/components' % team_user_id)
    assert components.status_code == 401
