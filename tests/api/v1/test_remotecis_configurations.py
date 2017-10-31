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


def test_create_configuration(user_admin, remoteci_user_id, topic_user_id):
    url = '/api/v1/remotecis/%s/rconfigurations' % remoteci_user_id
    rc = user_admin.post(url, data={
        'name': 'cname',
        'topic_id': topic_user_id,
        'component_types': ['kikoo', 'lol'],
        'data': {'lol': 'lol'}
    })
    assert rc.status_code == 201
    rc = rc.data
    rc_id = rc['rconfiguration']['id']
    grc = user_admin.get('/api/v1/remotecis/%s/rconfigurations/%s' %
                         (remoteci_user_id, rc_id)).data
    assert grc['rconfiguration']['name'] == 'cname'
    assert grc['rconfiguration']['topic_id'] == topic_user_id
    assert grc['rconfiguration']['data'] == {'lol': 'lol'}
    assert grc['rconfiguration']['component_types'] == ['kikoo', 'lol']


def test_get_all_configurations(user_admin, user, remoteci_user_id,
                                topic_user_id):
    for i in range(3):
        rc = user_admin.post('/api/v1/remotecis/%s/rconfigurations' %
                             remoteci_user_id,
                             data={'name': 'cname%s' % i,
                                   'topic_id': topic_user_id,
                                   'component_types': ['kikoo%s' % i],
                                   'data': {'lol': 'lol%s' % i}})
        assert rc.status_code == 201

    all_rcs = user.get('/api/v1/remotecis/%s/rconfigurations?sort=created_at' %
                       remoteci_user_id).data
    for i in range(3):
        rc = all_rcs['rconfigurations'][i]
        assert rc['name'] == 'cname%s' % i
        assert rc['data'] == {'lol': 'lol%s' % i}
        assert rc['component_types'] == ['kikoo%s' % i]

    assert all_rcs['_meta']['count'] == 3


def test_delete_configuration_by_id(user_admin, user, remoteci_user_id,
                                    topic_user_id):
    rc_ids = []
    for i in range(3):
        rc = user_admin.post('/api/v1/remotecis/%s/rconfigurations' %
                             remoteci_user_id,
                             data={'name': 'cname%s' % i,
                                   'topic_id': topic_user_id,
                                   'data': {'lol': 'lol%s' % i}})
        rc_ids.append(rc.data['rconfiguration']['id'])
        assert rc.status_code == 201

    all_rcs = user.get('/api/v1/remotecis/%s/rconfigurations' %
                       remoteci_user_id).data
    assert all_rcs['_meta']['count'] == 3

    for i in range(3):
        drc = user_admin.delete('/api/v1/remotecis/%s/rconfigurations/%s' %
                                (remoteci_user_id, rc_ids[i]))
        assert drc.status_code == 204
        all_rcs = user.get('/api/v1/remotecis/%s/rconfigurations' %
                           remoteci_user_id).data
        # (i+1) since range(3) = 0,1,2
        assert all_rcs['_meta']['count'] == (3 - (i + 1))


def test_purge(admin, user_admin, remoteci_user_id, topic_user_id):
    for i in range(3):
        rc = user_admin.post('/api/v1/remotecis/%s/rconfigurations' %
                             remoteci_user_id,
                             data={'name': 'cname%s' % i,
                                   'topic_id': topic_user_id,
                                   'data': {'lol': 'lol%s' % i}})
        assert rc.status_code == 201
        url = '/api/v1/remotecis/%s/rconfigurations/%s' % \
              (remoteci_user_id, rc.data['rconfiguration']['id'])
        dr = user_admin.delete(url)
        assert dr.status_code == 204

    prg = admin.get('/api/v1/remotecis/rconfigurations/purge')
    assert prg.data['_meta']['count'] == 3

    prg = admin.post('/api/v1/remotecis/rconfigurations/purge')
    assert prg.status_code == 204

    prg = admin.get('/api/v1/remotecis/rconfigurations/purge')
    assert prg.data['_meta']['count'] == 0
