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


def test_attach_tag_to_components(admin, component_id):
    tag = admin.post('/api/v1/components/%s/tags' % component_id,
                     data={'value': 'test'}).data
    result = admin.get('/api/v1/components/%s/tags' % component_id).data
    assert result['tags'][0]['value'] == tag['tag']['value']


def test_delete_tag_on_component(admin, component_id):
    tag = admin.post('/api/v1/components/%s/tags' % component_id,
                     data={'value': 'test'}).data
    result = admin.get('/api/v1/components/%s/tags' % component_id).data
    assert result['tags'][0]['value'] == tag['tag']['value']
