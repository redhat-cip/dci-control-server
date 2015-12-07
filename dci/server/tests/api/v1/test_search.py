# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Red Hat, Inc
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


def test_index_file(admin, jobstate_id, team_id):
    content = 'kikoololol'
    file = admin.post('/api/v1/files',
                      data={'jobstate_id': jobstate_id, 'team_id': team_id,
                            'content': content,
                            'name': 'kikoololol'}).data
    file_id = file['file']['id']
    file = admin.post('/api/v1/search',
                      data={'pattern': content}).data
    assert file_id == file['logs']['hits'][0]['_id']


def test_get_indexed_file_isolation(user, admin, jobstate_id, team_id,
                                    remoteci_id):
    content = 'kikoolol_isolation'
    admin.post('/api/v1/files',
               data={'jobstate_id': jobstate_id, 'team_id': team_id,
                     'content': content,
                     'name': 'kikoololol'}).data
    search = user.post('/api/v1/search',
                       data={'pattern': content}).data
    assert search['logs']['total'] == 0
