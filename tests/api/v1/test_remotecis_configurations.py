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


def test_create_configuration(user, remoteci_user_id, topic_user_id):
    rc = user.post('/api/v1/remotecis/%s/configurations' % remoteci_user_id,
                   data={'name': 'cname',
                         'topic_id': topic_user_id,
                         'component_types': ['kikoo', 'lol'],
                         'data': {'lol': 'lol'}})
    assert rc.status_code == 201
    rc = rc.data
    rc_id = rc['configuration']['id']
    grc = user.get('/api/v1/remotecis/%s/configurations/%s' %
                   (remoteci_user_id, rc_id)).data
    assert grc['configuration']['name'] == 'cname'
    assert grc['configuration']['topic_id'] == topic_user_id
    assert grc['configuration']['data'] == {'lol': 'lol'}
    assert grc['configuration']['component_types'] == ['kikoo', 'lol']


def test_put_configuration(user, remoteci_user_id,
                           remoteci_configuration_user_id, topic_user_id):

    grc = user.get('/api/v1/remotecis/%s/configurations/%s' %
                   (remoteci_user_id, remoteci_configuration_user_id)).data
    grc_etag = grc['configuration']['etag']
    rc = user.put('/api/v1/remotecis/%s/configurations/%s' %
                  (remoteci_user_id, remoteci_configuration_user_id),
                  headers={'If-match': grc_etag},
                  data={'name': 'kikooname',
                        'component_types': ['mdr'],
                        'data': {'lol2': 'lol2'}})
    assert rc.status_code == 204
    grc = user.get('/api/v1/remotecis/%s/configurations/%s' %
                   (remoteci_user_id, remoteci_configuration_user_id)).data
    assert grc['configuration']['name'] == 'kikooname'
    assert grc['configuration']['topic_id'] == topic_user_id
    assert grc['configuration']['data'] == {'lol2': 'lol2'}
    assert grc['configuration']['component_types'] == ['mdr']


def test_get_all_configurations(user, remoteci_user_id, topic_user_id):
    for i in range(3):
        rc = user.post('/api/v1/remotecis/%s/configurations' %
                       remoteci_user_id,
                       data={'name': 'cname%s' % i,
                             'topic_id': topic_user_id,
                             'component_types': ['kikoo%s' % i],
                             'data': {'lol': 'lol%s' % i}})
        assert rc.status_code == 201

    all_rcs = user.get('/api/v1/remotecis/%s/configurations?sort=created_at' %
                       remoteci_user_id).data
    for i in range(3):
        rc = all_rcs['configurations'][i]
        assert rc['name'] == 'cname%s' % i
        assert rc['data'] == {'lol': 'lol%s' % i}
        assert rc['component_types'] == ['kikoo%s' % i]

    assert all_rcs['_meta']['count'] == 3


def test_delete_configuration_by_id(user, remoteci_user_id, topic_user_id):
    rc_ids = []
    for i in range(3):
        rc = user.post('/api/v1/remotecis/%s/configurations' %
                       remoteci_user_id,
                       data={'name': 'cname%s' % i,
                             'topic_id': topic_user_id,
                             'data': {'lol': 'lol%s' % i}})
        rc_ids.append(rc.data['configuration']['id'])
        assert rc.status_code == 201

    all_rcs = user.get('/api/v1/remotecis/%s/configurations' %
                       remoteci_user_id).data
    assert all_rcs['_meta']['count'] == 3

    for i in range(3):
        drc = user.delete('/api/v1/remotecis/%s/configurations/%s' %
                          (remoteci_user_id, rc_ids[i]))
        assert drc.status_code == 204
        all_rcs = user.get('/api/v1/remotecis/%s/configurations' %
                           remoteci_user_id).data
        # (i+1) since range(3) = 0,1,2
        assert all_rcs['_meta']['count'] == (3 - (i + 1))
