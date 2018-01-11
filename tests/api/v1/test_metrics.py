# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Red Hat, Inc
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


def test_metrics_admin(admin, remoteci_context, remoteci_id, team_id, product):
    t = admin.post('/api/v1/topics',
                   data={'name': 'foo', 'product_id': product['id'],
                         'component_types': ['type1', 'type2']}).data
    t_id = t['topic']['id']
    admin.post('/api/v1/components',
               data={'name': '2017-05-27.1',
                     'type': 'type_1',
                     'topic_id': t_id})
    c = admin.post('/api/v1/components',
                   data={'name': '2017-06-01.3',
                         'type': 'type_2',
                         'topic_id': t_id}).data
    c_id = c['component']['id']
    admin.post('/api/v1/topics',
               data={'name': 'bar', 'product_id': product['id'],
                     'component_types': ['type1', 'type2']})
    remoteci_context.post('/api/v1/jobs', data={'components': [c_id]})
    remoteci_context.post('/api/v1/jobs', data={'components': [c_id]})
    res = admin.get('/api/v1/metrics/topics')
    foo = res.data['topics']['foo']
    bar = res.data['topics']['bar']
    assert res.status_code == 200
    assert len(res.data['topics']) == 2
    assert len(foo) == 2
    assert foo[0]['component'] == '2017-05-27.1'
    assert len(foo[0]['values']) == 0
    assert foo[1]['component'] == '2017-06-01.3'
    assert len(foo[1]['values']) == 2
    assert foo[0]['date'] < foo[1]['date']
    assert len(bar) == 0


def test_metrics_user(user):
    res = user.get('/api/v1/metrics/topics')
    assert res.status_code == 401
