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


def test_global_status(admin, remoteci_context, remoteci_user_id, product):
    topic = admin.post('/api/v1/topics',
                       data={
                           'name': 'OSP12',
                           'product_id': product['id'],
                           'component_types': ['puddle']
                       }).data['topic']
    admin.post('/api/v1/components',
               data={
                   'name': 'RH7-RHOS-12.0 2016-11-12.1',
                   'type': 'type_1',
                   'topic_id': topic['id']
               })
    component = admin.post('/api/v1/components',
                           data={
                               'name': 'RH7-RHOS-12.0 2016-11-13.1',
                               'type': 'type_1',
                               'topic_id': topic['id']}).data['component']
    remoteci_context.post('/api/v1/jobs',
                          data={'components': [component['id']]})
    remoteci_context.post('/api/v1/jobs',
                          data={'components': [component['id']]})
    global_status = admin.get('/api/v1/global_status').data
    stats = global_status['RH7-RHOS-12.0 2016-11-13.1']
    assert len(stats['jobs']) == 1
    assert stats['jobs'][0]['status'] == 'new'
    assert stats['jobs'][0]['remoteci_id'] == remoteci_user_id
    assert stats['topic_id'] == topic['id']
    assert stats['topic_name'] == topic['name']
