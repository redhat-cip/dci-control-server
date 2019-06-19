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
import mock
import pytest
import uuid
from dci import dci_config
from dci.api.v1 import components
from dci.stores import files_utils
from dci.common import exceptions as dci_exc


def test_create_components(admin, topic_id):
    data = {
        'name': 'pname',
        'type': 'gerrit_review',
        'url': 'http://example.com/',
        'topic_id': topic_id,
        'export_control': True,
        'state': 'active'}
    pc = admin.post('/api/v1/components', data=data).data
    pc_id = pc['component']['id']
    gc = admin.get('/api/v1/components/%s' % pc_id).data
    assert gc['component']['name'] == 'pname'
    assert gc['component']['state'] == 'active'


def test_create_components_already_exist(admin, topic_id):
    data = {'name': 'pname', 'type': 'gerrit_review', 'topic_id': topic_id}
    pstatus_code = admin.post('/api/v1/components', data=data).status_code
    assert pstatus_code == 201

    data = {'name': 'pname', 'type': 'gerrit_review', 'topic_id': topic_id}
    pstatus_code = admin.post('/api/v1/components', data=data).status_code
    assert pstatus_code == 409


def test_create_components_with_same_name_on_different_topics(admin, topic_id,
                                                              product):
    data = {'name': 'pname', 'type': 'gerrit_review', 'topic_id': topic_id}
    pstatus_code = admin.post('/api/v1/components', data=data).status_code
    assert pstatus_code == 201

    topic2 = admin.post('/api/v1/topics',
                        data={'name': 'tname', 'product_id': product['id'],
                              'component_types': ['type1', 'type2']}).data
    topic_id2 = topic2['topic']['id']

    data = {'name': 'pname', 'type': 'gerrit_review', 'topic_id': topic_id2}
    pstatus_code = admin.post('/api/v1/components', data=data).status_code
    assert pstatus_code == 201


def test_create_components_with_same_name_on_same_topics(admin, topic_id):
    data = {'name': 'pname', 'type': 'gerrit_review', 'topic_id': topic_id}
    pstatus_code = admin.post('/api/v1/components', data=data).status_code
    assert pstatus_code == 201

    data = {'name': 'pname', 'type': 'gerrit_review', 'topic_id': topic_id}
    pstatus_code = admin.post('/api/v1/components', data=data).status_code
    assert pstatus_code == 409


def test_recreate_components_with_same_name_on_same_topics(admin, topic_id):
    """ The goal of this test is to verify that we can:
        - create a component, delete it, then create another component with
          the same name as the previous one
        - create, then delete, then create, then delete, multiple times a
          component with the same name
    """
    for n in range(3):
        data = {'name': 'pouet', 'type': 'gerrit_review', 'topic_id': topic_id}
        result = admin.post('/api/v1/components', data=data)
        assert result.status_code == 201

        result = admin.delete('/api/v1/components/%s' %
                              result.data['component']['id'])
        assert result.status_code == 204


def test_create_components_with_same_name_and_different_type(admin, topic_id):
    data = {'name': 'pname', 'type': 'first_type', 'topic_id': topic_id}
    pstatus_code = admin.post('/api/v1/components', data=data).status_code
    assert pstatus_code == 201

    data = {'name': 'pname', 'type': 'second_type', 'topic_id': topic_id}
    pstatus_code = admin.post('/api/v1/components', data=data).status_code
    assert pstatus_code == 201


def test_get_all_components(admin, topic_id):
    created_c_ids = []
    for i in range(5):
        pc = admin.post('/api/v1/components',
                        data={'name': 'pname%s' % uuid.uuid4(),
                              'type': 'gerrit_review',
                              'topic_id': topic_id}).data
        created_c_ids.append(pc['component']['id'])
    created_c_ids.sort()

    db_all_cs = admin.get('/api/v1/topics/%s/components' % topic_id).data
    db_all_cs = db_all_cs['components']
    db_all_cs_ids = [db_ct['id'] for db_ct in db_all_cs]
    db_all_cs_ids.sort()

    assert db_all_cs_ids == created_c_ids


def test_get_all_components_not_in_topic(admin, user, product_openstack):
    topic = admin.post('/api/v1/topics',
                       data={'name': 'topic_test',
                             'product_id': product_openstack['id'],
                             'component_types': ['type1', 'type2']}).data
    topic_id = topic['topic']['id']
    res = user.get(
        '/api/v1/topics/%s/components' % topic_id)
    assert res.status_code == 401
    assert res.data['message'] == 'Operation not authorized.'


def test_get_all_components_with_pagination(admin, topic_id):
    # create 20 component types and check meta data count
    for i in range(20):
        admin.post('/api/v1/components',
                   data={'name': 'pname%s' % uuid.uuid4(),
                         'type': 'gerrit_review',
                         'topic_id': topic_id})
    cs = admin.get('/api/v1/topics/%s/components' % topic_id).data
    assert cs['_meta']['count'] == 20

    # verify limit and offset are working well
    for i in range(4):
        cs = admin.get(
            '/api/v1/topics/%s/components?limit=5&offset=%s' %
            (topic_id, (i * 5))).data
        assert len(cs['components']) == 5

    # if offset is out of bound, the api returns an empty list
    cs = admin.get(
        '/api/v1/topics/%s/components?limit=5&offset=300' % topic_id)
    assert cs.status_code == 200
    assert cs.data['components'] == []


def test_get_all_components_with_where(admin, topic_id):
    pc = admin.post('/api/v1/components',
                    data={'name': 'pname1',
                          'type': 'gerrit_review',
                          'topic_id': topic_id}).data
    pc_id = pc['component']['id']

    db_c = admin.get(
        '/api/v1/topics/%s/components?where=id:%s' % (topic_id, pc_id)).data
    db_c_id = db_c['components'][0]['id']
    assert db_c_id == pc_id

    db_c = admin.get(
        '/api/v1/topics/%s/components?where=name:pname1' % topic_id).data
    db_c_id = db_c['components'][0]['id']
    assert db_c_id == pc_id


def test_where_invalid(admin, topic_id):
    err = admin.get('/api/v1/topics/%s/components?where=id' % topic_id)

    assert err.status_code == 400
    assert err.data['message'] == "Request malformed"
    assert err.data['payload']['error'] == "where: 'id' is not a 'key value csv'"


def test_get_component_by_id_or_name(admin, topic_id):
    data = {'name': 'pname',
            'type': 'gerrit_review',
            'topic_id': topic_id,
            'export_control': True
            }
    pc = admin.post('/api/v1/components', data=data).data
    pc_id = pc['component']['id']

    # get by uuid
    created_ct = admin.get('/api/v1/components/%s' % pc_id)
    assert created_ct.status_code == 200

    created_ct = created_ct.data
    assert created_ct['component']['id'] == pc_id


def test_get_component_not_found(admin):
    result = admin.get('/api/v1/components/ptdr')
    assert result.status_code == 404


def test_delete_component_by_id(admin, topic_id, user, topic_user_id):

    authorized_contexts = [{'user': admin, 'topic': topic_id},
                           {'user': user, 'topic': topic_user_id}]

    for context in authorized_contexts:
        data = {'name': 'pname',
                'type': 'gerrit_review',
                'topic_id': context['topic'],
                'export_control': True}
        pc = context['user'].post('/api/v1/components', data=data)
        pc_id = pc.data['component']['id']
        assert pc.status_code == 201

        created_ct = context['user'].get('/api/v1/components/%s' % pc_id)
        assert created_ct.status_code == 200

        deleted_ct = context['user'].delete('/api/v1/components/%s' % pc_id)
        assert deleted_ct.status_code == 204

        gct = context['user'].get('/api/v1/components/%s' % pc_id)
        assert gct.status_code == 404


def test_get_all_components_with_sort(admin, topic_id):
    # create 4 components ordered by created time
    data = {'name': "pname1", 'title': 'aaa',
            'type': 'gerrit_review',
            'topic_id': topic_id}
    ct_1_1 = admin.post('/api/v1/components', data=data).data['component']
    data = {'name': "pname2", 'title': 'aaa',
            'type': 'gerrit_review',
            'topic_id': topic_id}
    ct_1_2 = admin.post('/api/v1/components', data=data).data['component']
    data = {'name': "pname3", 'title': 'bbb',
            'type': 'gerrit_review',
            'topic_id': topic_id}
    ct_2_1 = admin.post('/api/v1/components', data=data).data['component']
    data = {'name': "pname4", 'title': 'bbb',
            'type': 'gerrit_review',
            'topic_id': topic_id}
    ct_2_2 = admin.post('/api/v1/components', data=data).data['component']

    cts = admin.get(
        '/api/v1/topics/%s/components?sort=created_at' % topic_id).data
    cts_id = [db_cts['id'] for db_cts in cts['components']]
    assert cts_id == [ct_1_1['id'], ct_1_2['id'], ct_2_1['id'], ct_2_2['id']]

    # sort by title first and then reverse by created_at
    cts = admin.get(
        '/api/v1/topics/%s/components?sort=title,-created_at' % topic_id).data
    cts_id = [db_cts['id'] for db_cts in cts['components']]
    assert cts_id == [ct_1_2['id'], ct_1_1['id'], ct_2_2['id'], ct_2_1['id']]


def test_delete_component_not_found(admin):
    result = admin.delete('/api/v1/components/%s' % uuid.uuid4(),
                          headers={'If-match': 'mdr'})
    assert result.status_code == 404


def test_put_component(admin, user, topic_id):
    data = {'name': "pname1", 'title': 'aaa',
            'type': 'gerrit_review',
            'topic_id': topic_id}

    ct_1 = admin.post('/api/v1/components', data=data).data['component']

    # Active component
    url = '/api/v1/components/%s' % ct_1['id']
    data = {'export_control': True}
    headers = {'If-match': ct_1['etag']}
    admin.put(url, data=data, headers=headers)

    ct_2 = admin.get('/api/v1/components/%s' % ct_1['id']).data['component']

    assert ct_1['etag'] != ct_2['etag']
    assert ct_1['export_control']
    assert ct_2['export_control']


def test_add_file_to_component(admin, topic_id):

    def create_ct(name):
        data = {'name': name, 'title': 'aaa',
                'type': 'gerrit_review',
                'topic_id': topic_id,
                'export_control': True}
        return admin.post(
            '/api/v1/components',
            data=data).data['component']

    ct_1 = create_ct('pname1')
    ct_2 = create_ct('pname2')

    cts = admin.get(
        '/api/v1/components/%s?embed=files' % ct_1['id']).data
    assert len(cts['component']['files']) == 0

    url = '/api/v1/components/%s/files' % ct_1['id']
    c_file = admin.post(url, data='lol')
    c_file_1_id = c_file.data['component_file']['id']
    url = '/api/v1/components/%s/files' % ct_2['id']
    c_file = admin.post(url, data='lol2')
    c_file_2_id = c_file.data['component_file']['id']

    assert c_file.status_code == 201
    l_file = admin.get(url)
    assert l_file.status_code == 200
    assert l_file.data['_meta']['count'] == 1
    assert l_file.data['component_files'][0]['component_id'] == ct_2['id']
    cts = admin.get(
        '/api/v1/components/%s?embed=files' % ct_1['id']).data
    assert len(cts['component']['files']) == 1
    assert cts['component']['files'][0]['size'] == 5

    cts = admin.get('/api/v1/components/%s/files' % ct_1['id']).data
    assert cts['component_files'][0]['id'] == c_file_1_id

    cts = admin.get('/api/v1/components/%s/files' % ct_2['id']).data
    assert cts['component_files'][0]['id'] == c_file_2_id


def test_download_file_from_component(admin, topic_id):
    data = {'name': "pname1", 'title': 'aaa',
            'type': 'gerrit_review',
            'topic_id': topic_id,
            'export_control': True}
    ct_1 = admin.post('/api/v1/components', data=data).data['component']

    url = '/api/v1/components/%s/files' % ct_1['id']
    data = "lollollel"
    c_file = admin.post(url, data=data).data['component_file']

    url = '/api/v1/components/%s/files/%s/content' % (ct_1['id'],
                                                      c_file['id'])
    d_file = admin.get(url)
    assert d_file.status_code == 200
    assert d_file.data == '"lollollel"'


def test_delete_file_from_component(admin, topic_id):
    data = {'name': "pname1", 'title': 'aaa',
            'type': 'gerrit_review',
            'topic_id': topic_id,
            'export_control': True}
    ct_1 = admin.post('/api/v1/components', data=data).data['component']

    url = '/api/v1/components/%s/files' % ct_1['id']
    data = "lol"
    c_file = admin.post(url, data=data).data['component_file']
    url = '/api/v1/components/%s/files' % ct_1['id']
    g_file = admin.get(url)
    assert g_file.data['_meta']['count'] == 1

    url = '/api/v1/components/%s/files/%s' % (ct_1['id'], c_file['id'])
    d_file = admin.delete(url)
    assert d_file.status_code == 204

    url = '/api/v1/components/%s/files' % ct_1['id']
    g_file = admin.get(url)
    assert g_file.data['_meta']['count'] == 0


def test_change_component_state(admin, topic_id):
    data = {
        'name': 'pname',
        'type': 'gerrit_review',
        'url': 'http://example.com/',
        'topic_id': topic_id,
        'export_control': True,
        'state': 'active'}
    pc = admin.post('/api/v1/components', data=data).data
    pc_id = pc['component']['id']

    t = admin.get('/api/v1/components/' + pc_id).data['component']
    data = {'state': 'inactive'}
    r = admin.put('/api/v1/components/' + pc_id,
                  data=data,
                  headers={'If-match': t['etag']})
    assert r.status_code == 200
    assert r.data['component']['state'] == 'inactive'


def test_change_component_to_invalid_state(admin, topic_id):
    data = {
        'name': 'pname',
        'type': 'gerrit_review',
        'url': 'http://example.com/',
        'topic_id': topic_id,
        'export_control': True,
        'state': 'active'}
    pc = admin.post('/api/v1/components', data=data).data
    pc_id = pc['component']['id']

    t = admin.get('/api/v1/components/' + pc_id).data['component']
    data = {'state': 'kikoolol'}
    r = admin.put('/api/v1/components/' + pc_id,
                  data=data,
                  headers={'If-match': t['etag']})
    assert r.status_code == 400
    current_component = admin.get('/api/v1/components/' + pc_id)
    assert current_component.status_code == 200
    assert current_component.data['component']['state'] == 'active'


def test_component_success_update_field_by_field(admin, topic_id):
    data = {
        'name': 'pname',
        'type': 'gerrit_review',
        'topic_id': topic_id
    }
    c = admin.post('/api/v1/components', data=data).data['component']

    admin.put('/api/v1/components/%s' % c['id'],
              data={'state': 'inactive'},
              headers={'If-match': c['etag']})

    c = admin.get('/api/v1/components/%s' % c['id']).data['component']

    assert c['name'] == 'pname'
    assert c['state'] == 'inactive'
    assert c['title'] is None

    c = admin.put('/api/v1/components/%s' % c['id'],
                  data={'name': 'pname2'},
                  headers={'If-match': c['etag']}).data['component']

    assert c['name'] == 'pname2'
    assert c['state'] == 'inactive'
    assert c['title'] is None

    admin.put('/api/v1/components/%s' % c['id'],
              data={'title': 'a new title'},
              headers={'If-match': c['etag']})

    c = admin.get('/api/v1/components/%s' % c['id']).data['component']

    assert c['name'] == 'pname2'
    assert c['state'] == 'inactive'
    assert c['title'] == 'a new title'


def test_get_component_types_from_topic(admin, engine, topic):
    expected_component_types = ['puddle_osp']
    component_types = components.get_component_types_from_topic(topic['id'],
                                                                db_conn=engine)
    assert expected_component_types == component_types


def _create_rconfiguration(admin, remoteci_id, data):
    url = '/api/v1/remotecis/%s/rconfigurations' % remoteci_id
    r = admin.post(url, data=data)
    assert r.status_code == 201
    return r.data['rconfiguration']


def test_get_component_types(engine, admin, remoteci_context, topic):
    remoteci = remoteci_context.get('/api/v1/identity').data['identity']

    component_types, _ = components.get_component_types(topic['id'],
                                                        remoteci['id'],
                                                        db_conn=engine)
    # use topic's component types
    expected_component_types = ['puddle_osp']
    assert expected_component_types == component_types

    # use rconfiguration's component types
    expected_component_types = ['kikoolol', 'mdr']
    rconfiguration = {'name': 'rc', 'topic_id': topic['id'],
                      'component_types': expected_component_types}
    _create_rconfiguration(admin, remoteci['id'], rconfiguration)
    component_types, _ = components.get_component_types(topic['id'],
                                                        remoteci['id'],
                                                        db_conn=engine)
    assert expected_component_types == component_types


def create_component(admin, topic_id, ct, name):
    data = {'topic_id': topic_id,
            'name': name,
            'type': ct,
            'export_control': True}
    component = admin.post('/api/v1/components',
                           data=data).data
    return str(component['component']['id'])


def test_get_last_components_by_type(engine, admin, topic):

    components_ids = []
    for i in range(3):
        cid = create_component(admin, topic['id'], 'puddle_osp', 'name-%s' % i)
        components_ids.append(cid)

    last_components = components.get_last_components_by_type(
        ['puddle_osp'],
        topic_id=topic['id'],
        db_conn=engine)
    assert str(last_components[0]['id']) == components_ids[-1]


def test_verify_and_get_components_ids(engine, admin, topic, topic_user_id):
    # components types not valid
    with pytest.raises(dci_exc.DCIException):
        components.verify_and_get_components_ids(topic['id'], [],
                                                 ['puddle_osp'],
                                                 db_conn=engine)

    with pytest.raises(dci_exc.DCIException):
        components.verify_and_get_components_ids(topic['id'],
                                                 [str(uuid.uuid4())],
                                                 ['puddle_osp'],
                                                 db_conn=engine)

    # duplicated component types
    c1 = create_component(admin, topic_user_id, 'type1', 'n1')
    c2 = create_component(admin, topic_user_id, 'type1', 'n2')
    c3 = create_component(admin, topic_user_id, 'type2', 'n3')
    with pytest.raises(dci_exc.DCIException):
        components.verify_and_get_components_ids(
            topic_user_id,
            [c1, c2, c3],
            ['type_1', 'type_2', 'type_3'],
            db_conn=engine)

    cids = components.verify_and_get_components_ids(topic_user_id,
                                                    [c1, c3],
                                                    ['type_1', 'type_2'],
                                                    db_conn=engine)
    assert set(cids) == {c1, c3}


def test_add_tags_components(admin, components_ids):
    pt = admin.post('/api/v1/components/%s/tags' % (components_ids[0]),
                    data={'name': 'my_tag'})
    assert pt.status_code == 201


def test_get_tags_components(admin, components_ids):
    gt = admin.get('/api/v1/components/%s/tags' % (components_ids[0]))
    count = gt.data['_meta']['count']

    for i in range(3):
        admin.post('/api/v1/components/%s/tags' % (components_ids[0]),
                   data={'name': 'name_%s' % i})
    gt = admin.get('/api/v1/components/%s/tags' % (components_ids[0]))
    assert gt.status_code == 200
    assert len(gt.data['tags']) == count + 3


def test_delete_tags_components(admin, components_ids):
    pt = admin.post('/api/v1/components/%s/tags' % (components_ids[0]),
                    data={'name': 'my_tag'})
    tag_id = pt.data['tag']['id']
    assert pt.status_code == 201
    pt = admin.delete('/api/v1/components/%s/tags/%s' % (components_ids[0],
                                                         tag_id))
    assert pt.status_code == 204

    gt = admin.get('/api/v1/components/%s/tags' % (components_ids[0]))
    assert gt.status_code == 200
    count = gt.data['_meta']['count']
    assert count == 0


def test_purge(admin, components_user_ids, topic_user_id):
    component_id = components_user_ids[0]
    store = dci_config.get_store('components')

    url = '/api/v1/components/%s/files' % component_id
    c_file1 = admin.post(url, data='lol')
    assert c_file1.status_code == 201

    path1 = files_utils.build_file_path(topic_user_id,
                                        component_id,
                                        c_file1.data['component_file']['id'])
    store.get(path1)

    url = '/api/v1/components/%s/files' % component_id
    c_file2 = admin.post(url, data='lol')
    assert c_file2.status_code == 201

    path2 = files_utils.build_file_path(topic_user_id,
                                        component_id,
                                        c_file2.data['component_file']['id'])
    store.get(path2)

    admin.delete('/api/v1/components/%s' % component_id)
    to_purge = admin.get('/api/v1/components/purge').data
    assert len(to_purge['components']) == 1
    c_purged = admin.post('/api/v1/components/purge')
    assert c_purged.status_code == 204

    with pytest.raises(dci_exc.StoreExceptions):
        store.get(path1)

    with pytest.raises(dci_exc.StoreExceptions):
        store.get(path2)

    to_purge = admin.get('/api/v1/components/purge').data
    assert len(to_purge['components']) == 0


def test_purge_failure(admin, components_user_ids, topic_user_id):
    component_id = components_user_ids[0]

    url = '/api/v1/components/%s/files' % component_id
    c_file1 = admin.post(url, data='lol')
    assert c_file1.status_code == 201

    c_files = admin.get('/api/v1/components/%s/files' % component_id)
    assert len(c_files.data['component_files']) == 1

    d_component = admin.delete('/api/v1/components/%s' % component_id)
    assert d_component.status_code == 204
    to_purge = admin.get('/api/v1/components/purge').data
    assert len(to_purge['components']) == 1
    # purge will fail
    with mock.patch('dci.stores.filesystem.FileSystem.delete') as mock_delete:
        path1 = files_utils.build_file_path(topic_user_id,
                                            component_id,
                                            c_file1.data['component_file']['id'])  # noqa
        mock_delete.side_effect = dci_exc.StoreExceptions('error')
        purge_res = admin.post('/api/v1/components/purge')
        assert purge_res.status_code == 400
        store = dci_config.get_store('components')
        store.get(path1)
        to_purge = admin.get('/api/v1/components/purge').data
        assert len(to_purge['components']) == 1
