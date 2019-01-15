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

from dci.api.v1 import remotecis


def test_create_configuration(user_admin, remoteci_user_id, topic_user_id):
    rc = user_admin.post('/api/v1/remotecis/%s/rconfigurations' %
                         remoteci_user_id,
                         data={'name': 'cname',
                               'topic_id': topic_user_id,
                               'data': {'lol': 'lol'}})
    assert rc.status_code == 201
    assert rc.data['rconfiguration']['component_types'] is None

    rc = user_admin.post('/api/v1/remotecis/%s/rconfigurations' %
                         remoteci_user_id,
                         data={'name': 'cname',
                               'topic_id': topic_user_id,
                               'component_types': ['kikoo', 'lol'],
                               'data': {'lol': 'lol'}})
    assert rc.status_code == 201
    rc = rc.data
    rc_id = rc['rconfiguration']['id']
    grc = user_admin.get('/api/v1/remotecis/%s/rconfigurations/%s' %
                         (remoteci_user_id, rc_id)).data
    assert grc['rconfiguration']['name'] == 'cname'
    assert grc['rconfiguration']['topic_id'] == topic_user_id
    assert grc['rconfiguration']['data'] == {'lol': 'lol'}
    assert grc['rconfiguration']['component_types'] == ['kikoo', 'lol']


def test_get_all_configurations(user_admin, remoteci_user_id, topic_user_id):
    for i in range(3):
        rc = user_admin.post('/api/v1/remotecis/%s/rconfigurations' %
                             remoteci_user_id,
                             data={'name': 'cname%s' % i,
                                   'topic_id': topic_user_id,
                                   'component_types': ['kikoo%s' % i],
                                   'data': {'lol': 'lol%s' % i}})
        assert rc.status_code == 201

    all_rcs = user_admin.get(
        '/api/v1/remotecis/%s/rconfigurations?sort=created_at' %
        remoteci_user_id).data
    for i in range(3):
        rc = all_rcs['rconfigurations'][i]
        assert rc['name'] == 'cname%s' % i
        assert rc['data'] == {'lol': 'lol%s' % i}
        assert rc['component_types'] == ['kikoo%s' % i]

    assert all_rcs['_meta']['count'] == 3


def test_delete_configuration_by_id(user_admin, remoteci_user_id,
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

    all_rcs = user_admin.get('/api/v1/remotecis/%s/rconfigurations' %
                             remoteci_user_id).data
    assert all_rcs['_meta']['count'] == 3

    for i in range(3):
        drc = user_admin.delete('/api/v1/remotecis/%s/rconfigurations/%s' %
                                (remoteci_user_id, rc_ids[i]))
        assert drc.status_code == 204
        all_rcs = user_admin.get('/api/v1/remotecis/%s/rconfigurations' %
                                 remoteci_user_id).data
        # (i+1) since range(3) = 0,1,2
        assert all_rcs['_meta']['count'] == (3 - (i + 1))


def _create_rconfiguration(admin, remoteci_id, data):
    url = '/api/v1/remotecis/%s/rconfigurations' % remoteci_id
    r = admin.post(url, data=data)
    assert r.status_code == 201
    return r.data['rconfiguration']


def test_get_last_rconfiguration_id(engine, admin, remoteci_context, topic):

    remoteci = remoteci_context.get('/api/v1/identity').data['identity']
    rconfiguration = {'name': 'rc', 'topic_id': topic['id']}
    # create 3 rconfiguration and schedule 3 jobs
    for i in range(3):
        _create_rconfiguration(admin, remoteci['id'], rconfiguration)
    expected_rconfig_id = ""
    for i in range(3):
        r = remoteci_context.post(
            '/api/v1/jobs/schedule',
            data={'topic_id': topic['id']}
        )
        assert r.status_code == 201
        expected_rconfig_id = r.data['job']['rconfiguration_id']
    rconf_id = remotecis.get_last_rconfiguration_id(topic['id'],
                                                    remoteci['id'],
                                                    db_conn=engine)
    assert expected_rconfig_id == rconf_id


def test_get_remoteci_configuration(engine, admin, remoteci_context, topic):

    remoteci = remoteci_context.get('/api/v1/identity').data['identity']
    rconfiguration = {'name': 'rc', 'topic_id': topic['id']}
    # create 3 rconfiguration and schedule 3 jobs
    rconfig_ids = []
    for i in range(3):
        rconfig = _create_rconfiguration(admin, remoteci['id'], rconfiguration)
        rconfig_ids.append(rconfig['id'])
    # sort desc order
    rconfig_ids = rconfig_ids[::-1]

    last_scheduled_rconfig_id = ""
    for i in range(3):
        r = remoteci_context.post(
            '/api/v1/jobs/schedule',
            data={'topic_id': topic['id']}
        )
        assert r.status_code == 201
        last_scheduled_rconfig_id = r.data['job']['rconfiguration_id']

    rconf_id = remotecis.get_remoteci_configuration(topic['id'],
                                                    remoteci['id'],
                                                    db_conn=engine)['id']
    rconf_id = str(rconf_id)

    for i in range(3):
        if last_scheduled_rconfig_id == rconfig_ids[i]:
            assert rconf_id == rconfig_ids[i - 1]


def test_purge(user_admin, admin, remoteci_user_id, topic_user_id):
    for i in range(3):
        rc = user_admin.post('/api/v1/remotecis/%s/rconfigurations' %
                             remoteci_user_id,
                             data={'name': 'cname%s' % i,
                                   'topic_id': topic_user_id,
                                   'data': {'lol': 'lol%s' % i}})
        assert rc.status_code == 201
        dr = user_admin.delete('/api/v1/remotecis/%s/rconfigurations/%s' %
                               (remoteci_user_id,
                                rc.data['rconfiguration']['id']))
        assert dr.status_code == 204

    prg = admin.get('/api/v1/remotecis/rconfigurations/purge')
    assert prg.data['_meta']['count'] == 3

    prg = admin.post('/api/v1/remotecis/rconfigurations/purge')
    assert prg.status_code == 204

    prg = admin.get('/api/v1/remotecis/rconfigurations/purge')
    assert prg.data['_meta']['count'] == 0
