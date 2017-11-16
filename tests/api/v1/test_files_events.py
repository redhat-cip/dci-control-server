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

from dci.db import models
from tests import utils


def test_files_events_create(admin, user, jobstate_user_id, team_user_id,
                             reset_file_event):
    file_id = utils.post_file(user, jobstate_user_id,
                              utils.FileDesc('kikoolol', 'content'))
    f_events = admin.get('/api/v1/files_events/0')
    assert f_events.status_code == 200

    f_events_data = f_events.data
    assert f_events_data['files'][0]['event']['file_id'] == file_id
    assert f_events_data['files'][0]['event']['action'] == models.FILES_CREATE


def test_files_events_delete(admin, user, jobstate_user_id, team_user_id,
                             reset_file_event):
    file_id = utils.post_file(user, jobstate_user_id,
                              utils.FileDesc('kikoolol', 'content'))
    admin.delete('/api/v1/files/%s' % file_id)

    f_events = admin.get('/api/v1/files_events/1?sort=id')
    assert f_events.status_code == 200

    f_events_data = f_events.data
    assert f_events_data['files'][1]['event']['file_id'] == file_id
    assert f_events_data['files'][1]['event']['action'] == models.FILES_DELETE


def test_files_events_delete_from_sequence_number(admin, user,
                                                  jobstate_user_id,
                                                  team_user_id,
                                                  reset_file_event):
    for i in range(5):
        utils.post_file(user, jobstate_user_id,
                        utils.FileDesc('kikoolol%s' % i, 'content%s' % i))
    f_events = admin.get('/api/v1/files_events/0').data
    assert len(f_events['files']) == 5

    admin.delete('/api/v1/files_events/3')

    f_events = admin.get('/api/v1/files_events/0').data
    assert len(f_events['files']) == 2


def test_files_events_user_unauthorized(user):
    f_events = user.get('/api/v1/files_events/0')
    assert f_events.status_code == 401
