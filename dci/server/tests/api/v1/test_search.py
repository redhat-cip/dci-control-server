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


def test_search_indexed_file(admin, jobstate_id, team_id, file_id):
    file = admin.post('/api/v1/search',
                      data={'pattern': 'kikoolol',
                            'refresh': True}).data
    result = [item for item in file['logs']['hits']
              if item["_id"] == file_id]

    assert file_id == result[0]["_id"]


def test_get_indexed_file_isolation(user, admin, jobstate_id, team_id,
                                    remoteci_id, file_id):
    search = user.get('/api/v1/search/%s' % file_id).data
    assert search == {'logs': {}}
