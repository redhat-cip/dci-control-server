# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Red Hat, Inc
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

from dci.api.v1 import scheduler


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
        print(r.data)
        expected_rconfig_id = r.data['job']['rconfiguration_id']
    rconf_id = scheduler.get_last_rconfiguration_id(topic['id'],
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

    rconf_id = scheduler.get_remoteci_configuration(topic['id'],
                                                    remoteci['id'],
                                                    db_conn=engine)['id']
    rconf_id = str(rconf_id)

    for i in range(3):
        if last_scheduled_rconfig_id == rconfig_ids[i]:
            assert rconf_id == rconfig_ids[i - 1]


def test_get_component_types_from_topic(admin, engine, topic):
    expected_component_types = ['puddle_osp']
    component_types = scheduler.get_component_types_from_topic(topic['id'],
                                                               db_conn=engine)
    assert expected_component_types == component_types


def test_get_component_types(engine, admin, remoteci_context, topic):
    remoteci = remoteci_context.get('/api/v1/identity').data['identity']

    component_types, _ = scheduler.get_component_types(topic['id'],
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
    component_types, _ = scheduler.get_component_types(topic['id'],
                                                       remoteci['id'],
                                                       db_conn=engine)
    assert expected_component_types == component_types


def test_get_last_components():
    pass


def test_get_components_from_ids():
    pass


def test_verify_and_get_components_ids():
    pass


def test_kill_existing_jobs():
    pass
