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

from dci.api.v1 import remotecis
from dci.api.v1 import scheduler
from dci.common import exceptions as dci_exc

import pytest
import uuid


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


def create_component(admin, topic_id, ct, name):
    data = {'topic_id': topic_id,
            'name': name,
            'type': ct,
            'export_control': True}
    component = admin.post('/api/v1/components',
                           data=data).data
    return str(component['component']['id'])


def test_get_last_components(engine, admin, topic):

    components_ids = []
    for i in range(3):
        cid = create_component(admin, topic['id'], 'puddle_osp', 'name-%s' % i)
        components_ids.append(cid)

    last_components = scheduler.get_last_components(['puddle_osp'],
                                                    topic_id=topic['id'],
                                                    db_conn=engine)
    assert str(last_components[0]) == components_ids[-1]


def test_verify_and_get_components_ids(engine, admin, topic, topic_user_id):
    # components types not valid
    with pytest.raises(dci_exc.DCIException):
        scheduler.verify_and_get_components_ids(topic['id'], [],
                                                ['puddle_osp'],
                                                db_conn=engine)

    with pytest.raises(dci_exc.DCIException):
        scheduler.verify_and_get_components_ids(topic['id'],
                                                [str(uuid.uuid4())],
                                                ['puddle_osp'],
                                                db_conn=engine)

    # duplicated component types
    c1 = create_component(admin, topic_user_id, 'type1', 'n1')
    c2 = create_component(admin, topic_user_id, 'type1', 'n2')
    c3 = create_component(admin, topic_user_id, 'type2', 'n3')
    with pytest.raises(dci_exc.DCIException):
        scheduler.verify_and_get_components_ids(topic_user_id,
                                                [c1, c2, c3],
                                                ['type_1', 'type_2', 'type_3'],
                                                db_conn=engine)

    cids = scheduler.verify_and_get_components_ids(topic_user_id,
                                                   [c1, c3],
                                                   ['type_1', 'type_2'],
                                                   db_conn=engine)
    assert set(cids) == {c1, c3}


def test_kill_existing_jobs(engine, admin, remoteci_context, topic):
    remoteci = remoteci_context.get('/api/v1/identity').data['identity']
    job = remoteci_context.post(
        '/api/v1/jobs/schedule',
        data={'topic_id': topic['id']}
    )
    assert job.status_code == 201
    job_id = job.data['job']['id']

    job = remoteci_context.get('/api/v1/jobs/%s' % job_id)
    assert job.status_code == 200
    assert job.data['job']['status'] == 'new'

    remotecis.kill_existing_jobs(remoteci['id'], db_conn=engine)

    job = remoteci_context.get('/api/v1/jobs/%s' % job_id)
    assert job.status_code == 200
    assert job.data['job']['status'] == 'killed'
