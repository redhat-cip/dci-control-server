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

from __future__ import unicode_literals
import pytest
import mock
import six

from dci.api.v1.files import get_file_info_from_headers
from dci.stores.swift import Swift
from dci.common import utils

import collections

SWIFT = 'dci.stores.swift.Swift'

FileDesc = collections.namedtuple('FileDesc', ['name', 'content'])


def post_file(client, jobstate_id, file_desc):
    with mock.patch(SWIFT, spec=Swift) as mock_swift:

        mockito = mock.MagicMock()

        head_result = {
            'etag': utils.gen_etag(),
            'content-type': "stream",
            'content-length': 7
        }

        mockito.head.return_value = head_result
        mock_swift.return_value = mockito
        headers = {'DCI-JOBSTATE-ID': jobstate_id, 'DCI-NAME': file_desc.name,
                   'Content-Type': 'text/plain'}
        res = client.post('/api/v1/files',
                          headers=headers,
                          data=file_desc.content)

        return res.data['file']['id']


def test_create_files(admin, jobstate_id, team_admin_id):
    file_id = post_file(admin, jobstate_id, FileDesc('kikoolol', 'content'))

    file = admin.get('/api/v1/files/%s' % file_id).data['file']

    assert file['name'] == 'kikoolol'
    assert file['size'] == 7


def test_create_files_jobstate_id_and_job_id_missing(admin, team_admin_id):
    file = admin.post('/api/v1/files', headers={'DCI-NAME': 'kikoolol'},
                      data='content')
    assert file.status_code == 400


def test_get_all_files(admin, jobstate_id):
    file_1 = post_file(admin, jobstate_id, FileDesc('kikoolol1', ''))
    file_2 = post_file(admin, jobstate_id, FileDesc('kikoolol2', ''))

    db_all_files = admin.get('/api/v1/files?sort=created_at').data
    db_all_files = db_all_files['files']
    db_all_files_ids = [file['id'] for file in db_all_files]

    assert db_all_files_ids == [file_1, file_2]


def test_get_all_files_with_pagination(admin, jobstate_id):
    # create 4 files types and check meta count
    for i in range(4):
        post_file(admin, jobstate_id, FileDesc('lol%d' % i, ''))

    # check meta count
    files = admin.get('/api/v1/files').data
    assert files['_meta']['count'] == 4

    # verify limit and offset are working well
    files = admin.get('/api/v1/files?limit=2&offset=0').data
    assert len(files['files']) == 2

    files = admin.get('/api/v1/files?limit=2&offset=2').data
    assert len(files['files']) == 2

    # if offset is out of bound, the api returns an empty list
    files = admin.get('/api/v1/files?limit=5&offset=300')
    assert files.status_code == 200
    assert files.data['files'] == []


def test_get_all_files_with_embed(admin, jobstate_id, team_admin_id, job_id):
    post_file(admin, jobstate_id, FileDesc('lol1', ''))
    post_file(admin, jobstate_id, FileDesc('lol2', ''))

    # verify embed
    files = admin.get('/api/v1/files?embed=team,jobstate,jobstate.job').data

    for file in files['files']:
        assert 'team' in file
        assert file['team']['id'] == team_admin_id
        assert 'jobstate' in file
        assert file['jobstate']['id'] == jobstate_id
        assert file['jobstate']['job']['id'] == job_id


def test_get_all_files_with_where(admin, jobstate_id):
    file_id = post_file(admin, jobstate_id, FileDesc('lol1', ''))

    db_job = admin.get('/api/v1/files?where=id:%s' % file_id).data
    db_job_id = db_job['files'][0]['id']
    assert db_job_id == file_id

    db_job = admin.get('/api/v1/files?where=name:lol1').data
    db_job_id = db_job['files'][0]['id']
    assert db_job_id == file_id


def test_where_invalid(admin):
    err = admin.get('/api/v1/files?where=id')

    assert err.status_code == 400
    assert err.data == {
        'status_code': 400,
        'message': 'Invalid where key: "id"',
        'payload': {
            'error': 'where key must have the following form "key:value"'
        }
    }


def test_get_all_files_with_sort(admin, jobstate_id):
    # create 4 files ordered by created time
    file_1_1 = post_file(admin, jobstate_id, FileDesc('a', ''))
    file_1_2 = post_file(admin, jobstate_id, FileDesc('a', ''))
    file_2_1 = post_file(admin, jobstate_id, FileDesc('b', ''))
    file_2_2 = post_file(admin, jobstate_id, FileDesc('b', ''))

    files = admin.get('/api/v1/files?sort=created_at').data
    files = [file['id'] for file in files['files']]
    assert files == [file_1_1, file_1_2, file_2_1, file_2_2]

    # sort by name first and then reverse by created_at
    files = admin.get('/api/v1/files?sort=name,-created_at').data
    files_ids = [file['id'] for file in files['files']]
    assert files_ids == [file_1_2, file_1_1, file_2_2, file_2_1]


def test_get_file_by_id(admin, jobstate_id):
    file_id = post_file(admin, jobstate_id, FileDesc('kikoolol', ''))

    # get by uuid
    created_file = admin.get('/api/v1/files/%s' % file_id)
    assert created_file.status_code == 200
    assert created_file.data['file']['name'] == 'kikoolol'


def test_get_file_not_found(admin):
    result = admin.get('/api/v1/files/ptdr')
    assert result.status_code == 404


def test_get_file_with_embed(admin, jobstate_id, team_admin_id):
    with mock.patch(SWIFT, spec=Swift) as mock_swift:

        mockito = mock.MagicMock()

        head_result = {
            'etag': utils.gen_etag(),
            'content-type': "stream",
            'content-length': 7,
        }

        mockito.head.return_value = head_result
        mock_swift.return_value = mockito
        pt = admin.get('/api/v1/teams/%s' % team_admin_id).data
        headers = {'DCI-JOBSTATE-ID': jobstate_id, 'DCI-NAME': 'kikoolol'}
        file = admin.post('/api/v1/files', headers=headers).data

        file_id = file['file']['id']
        file['file']['team'] = pt['team']

        # verify embed
        file_embed = admin.get('/api/v1/files/%s?embed=team' % file_id).data
        assert file == file_embed


def test_get_file_with_embed_not_valid(admin, jobstate_id):
    file_id = post_file(admin, jobstate_id, FileDesc('name', ''))
    file = admin.get('/api/v1/files/%s?embed=mdr' % file_id)
    assert file.status_code == 400


def test_delete_file_by_id(admin, jobstate_id):
    file_id = post_file(admin, jobstate_id, FileDesc('name', ''))
    url = '/api/v1/files/%s' % file_id

    created_file = admin.get(url)
    assert created_file.status_code == 200

    deleted_file = admin.delete(url)
    assert deleted_file.status_code == 204

    gfile = admin.get(url)
    assert gfile.status_code == 404


# Tests for the isolation


def test_create_file_as_user(user, jobstate_user_id):
    with mock.patch(SWIFT, spec=Swift) as mock_swift:

        mockito = mock.MagicMock()

        head_result = {
            'etag': utils.gen_etag(),
            'content-type': "stream",
            'content-length': 7
        }

        mockito.head.return_value = head_result
        mock_swift.return_value = mockito
        headers = {'DCI-JOBSTATE-ID': jobstate_user_id, 'DCI-NAME': 'name'}
        file = user.post('/api/v1/files', headers=headers)
        assert file.status_code == 201


@pytest.mark.usefixtures('file_id', 'file_user_id')
def test_get_all_files_as_user(user, team_user_id):
    files = user.get('/api/v1/files')
    assert files.status_code == 200
    assert files.data['_meta']['count']
    for file in files.data['files']:
        assert file['team_id'] == team_user_id


@pytest.mark.usefixtures('file_id', 'file_user_id')
def test_get_all_files_as_product_owner(product_owner, team_user_id):
    files = product_owner.get('/api/v1/files')
    assert files.status_code == 200
    assert files.data['_meta']['count']
    for file in files.data['files']:
        assert file['team_id'] == team_user_id


def test_get_file_as_user(user, file_id, jobstate_user_id):
    with mock.patch(SWIFT, spec=Swift) as mock_swift:

        mockito = mock.MagicMock()

        head_result = {
            'etag': utils.gen_etag(),
            'content-type': "stream",
            'content-length': 7
        }

        mockito.head.return_value = head_result
        mock_swift.return_value = mockito
        file = user.get('/api/v1/files/%s' % file_id)
        assert file.status_code == 404

        headers = {'DCI-JOBSTATE-ID': jobstate_user_id,
                   'DCI-NAME': 'name'}
        file = user.post('/api/v1/files', headers=headers).data
        file_id = file['file']['id']
        file = user.get('/api/v1/files/%s' % file_id)
        assert file.status_code == 200


def test_delete_file_as_user(user, admin, jobstate_user_id,
                             file_id):
    file_user_id = post_file(user, jobstate_user_id, FileDesc('name2', ''))
    file_user = user.get('/api/v1/files/%s' % file_user_id)

    file_delete = user.delete('/api/v1/files/%s' % file_user_id)
    assert file_delete.status_code == 204

    file_user = admin.get('/api/v1/files/%s' % file_id)
    assert file_user.status_code == 200

    file_delete = user.delete('/api/v1/files/%s' % file_id)
    assert file_delete.status_code == 401


def test_get_file_content(admin, jobstate_id):
    with mock.patch(SWIFT, spec=Swift) as mock_swift:

        mockito = mock.MagicMock()

        head_result = {
            'etag': utils.gen_etag(),
            'content-type': "stream",
            'content-length': 7
        }

        mockito.head.return_value = head_result
        mockito.get.return_value = [
            head_result, six.StringIO("azertyuiop1234567890")]
        mock_swift.return_value = mockito
        data = "azertyuiop1234567890"
        file_id = post_file(admin, jobstate_id, FileDesc('foo', data))

        get_file = admin.get('/api/v1/files/%s/content' % file_id)

        assert get_file.status_code == 200
        assert get_file.data == data


def test_get_file_content_as_user(user, file_id, file_user_id):
    url = '/api/v1/files/%s/content'

    assert user.get(url % file_id).status_code == 401
    with mock.patch(SWIFT, spec=Swift) as mock_swift:

        mockito = mock.MagicMock()

        head_result = {
            'etag': utils.gen_etag(),
            'content-type': "stream",
            'content-length': 7
        }

        mockito.head.return_value = head_result
        mockito.get.return_value = [
            head_result, six.StringIO("azertyuiop1234567890")]
        mock_swift.return_value = mockito
        assert user.get(url % file_user_id).status_code == 200


def test_change_file_to_invalid_state(admin, file_id):
    t = admin.get('/api/v1/files/' + file_id).data['file']
    data = {'state': 'kikoolol'}
    r = admin.put('/api/v1/files/' + file_id,
                  data=data,
                  headers={'If-match': t['etag']})
    assert r.status_code == 405
    current_file = admin.get('/api/v1/files/' + file_id)
    assert current_file.status_code == 200
    assert current_file.data['file']['state'] == 'active'


def test_get_file_info_from_header():
    headers = {
        'DCI-Client-Info': '',
        'DCI-Auth-Signature': '',
        'Authorization': '',
        'DCI-Datetime': '',
        'mime': '',
        'Dci-Job-Id': ''
    }
    file_info = get_file_info_from_headers(headers)
    assert len(file_info.keys()) == 2
    assert 'mime' in file_info
    assert 'job_id' in file_info
