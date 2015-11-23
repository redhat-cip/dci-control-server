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


def test_create_files(admin, jobstate_id, team_id):
    file = admin.post('/api/v1/files',
                      data={'jobstate_id': jobstate_id, 'team_id': team_id,
                            'content': 'content', 'name': 'kikoolol'}).data
    file_id = file['file']['id']
    file = admin.get('/api/v1/files/%s' % file_id).data
    assert file['file']['name'] == 'kikoolol'


def test_put_files(admin, jobstate_id, team_id):
    file = admin.post('/api/v1/files',
                      data={'jobstate_id': jobstate_id, 'team_id': team_id,
                            'content': 'content', 'name': 'kikoolol'})
    file_id = file.data['file']['id']
    file_etag = file.headers.get("ETag")

    pfile = admin.put('/api/v1/files/%s' % file_id,
                      data={'name': 'ptdr', 'content': 'kijiji'},
                      headers={'If-match': file_etag})
    assert pfile.status_code == 204

    gfile = admin.get('/api/v1/files/%s' % file_id).data
    assert gfile['file']['name'] == 'ptdr'
    assert gfile['file']['content'] == 'kijiji'


def test_get_all_files(admin, jobstate_id, team_id):
    file_1 = admin.post('/api/v1/files',
                        data={'jobstate_id': jobstate_id, 'team_id': team_id,
                              'content': 'content', 'name': 'kikoolol1'}).data
    file_1_id = file_1['file']['id']

    file_2_2 = admin.post('/api/v1/files',
                          data={'jobstate_id': jobstate_id,
                                'team_id': team_id,
                                'content': 'content',
                                'name': 'kikoolol2'}).data
    file_2_id = file_2_2['file']['id']

    db_all_files = admin.get('/api/v1/files?sort=created_at').data
    db_all_files = db_all_files['files']
    db_all_files_ids = [file['id'] for file in db_all_files]

    assert db_all_files_ids == [file_1_id, file_2_id]


def test_get_all_files_with_pagination(admin, jobstate_id, team_id):
    # create 4 files types and check meta count
    data = {'jobstate_id': jobstate_id, 'team_id': team_id,
            'content': 'content', 'name': 'lol1'}
    admin.post('/api/v1/files', data=data)
    data = {'jobstate_id': jobstate_id, 'team_id': team_id,
            'content': 'content', 'name': 'lol2'}
    admin.post('/api/v1/files', data=data)
    data = {'jobstate_id': jobstate_id, 'team_id': team_id,
            'content': 'content', 'name': 'lol3'}
    admin.post('/api/v1/files', data=data)
    data = {'jobstate_id': jobstate_id, 'team_id': team_id,
            'content': 'content', 'name': 'lol4'}
    admin.post('/api/v1/files', data=data)

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


def test_get_all_files_with_embed(admin, jobstate_id, team_id, job_id):
    data = {'jobstate_id': jobstate_id, 'team_id': team_id,
            'content': 'content', 'name': 'lol1'}
    admin.post('/api/v1/files', data=data)
    data = {'jobstate_id': jobstate_id, 'team_id': team_id,
            'content': 'content', 'name': 'lol2'}
    admin.post('/api/v1/files', data=data)

    # verify embed
    files = admin.get('/api/v1/files?embed=team,jobstate,jobstate.job').data

    for file in files['files']:
        assert 'team_id' not in file
        assert 'team' in file
        assert file['team']['id'] == team_id
        assert 'jobstate_id' not in file
        assert 'jobstate' in file
        assert file['jobstate']['id'] == jobstate_id
        assert file['jobstate']['job']['id'] == job_id


def test_get_all_files_with_where(admin, jobstate_id, team_id):
    file = admin.post('/api/v1/files',
                      data={'jobstate_id': jobstate_id, 'team_id': team_id,
                            'content': 'content', 'name': 'lol1'}).data
    file_id = file['file']['id']

    db_job = admin.get('/api/v1/files?where=id:%s' % file_id).data
    db_job_id = db_job['files'][0]['id']
    assert db_job_id == file_id

    db_job = admin.get('/api/v1/files?where=name:lol1').data
    db_job_id = db_job['files'][0]['id']
    assert db_job_id == file_id


def test_get_all_files_with_sort(admin, jobstate_id, team_id):
    # create 4 files ordered by created time
    data = {'jobstate_id': jobstate_id, 'team_id': team_id,
            'content': 'content', 'name': 'a'}
    file_1_1 = admin.post('/api/v1/files', data=data).data['file']
    data = {'jobstate_id': jobstate_id, 'team_id': team_id,
            'content': 'content', 'name': 'a'}
    file_1_2 = admin.post('/api/v1/files', data=data).data['file']
    data = {'jobstate_id': jobstate_id, 'team_id': team_id,
            'content': 'content', 'name': 'b'}
    file_2_1 = admin.post('/api/v1/files', data=data).data['file']
    data = {'jobstate_id': jobstate_id, 'team_id': team_id,
            'content': 'content', 'name': 'b'}
    file_2_2 = admin.post('/api/v1/files', data=data).data['file']

    files = admin.get('/api/v1/files?sort=created_at').data
    assert files['files'] == [file_1_1, file_1_2, file_2_1, file_2_2]

    # sort by content first and then reverse by created_at
    files = admin.get('/api/v1/files?sort=name,-created_at').data
    assert files['files'] == [file_1_2, file_1_1, file_2_2, file_2_1]


def test_get_file_by_id_or_name(admin, jobstate_id, team_id):
    file = admin.post('/api/v1/files',
                      data={'jobstate_id': jobstate_id, 'team_id': team_id,
                            'content': 'content', 'name': 'kikoolol'}).data
    file_id = file['file']['id']

    # get by uuid
    created_file = admin.get('/api/v1/files/%s' % file_id)
    assert created_file.status_code == 200
    assert created_file.data['file']['name'] == 'kikoolol'

    # get by name
    created_file = admin.get('/api/v1/files/kikoolol')
    assert created_file.status_code == 200
    assert created_file.data['file']['name'] == 'kikoolol'


def test_get_file_not_found(admin):
    result = admin.get('/api/v1/files/ptdr')
    assert result.status_code == 404


def test_get_file_with_embed(admin, jobstate_id, team_id):
    pt = admin.get('/api/v1/teams/%s' % team_id).data
    file = admin.post('/api/v1/files',
                      data={'jobstate_id': jobstate_id, 'team_id': team_id,
                            'content': 'content', 'name': 'kikoolol'}).data
    file_id = file['file']['id']
    del file['file']['team_id']
    file['file'][u'team'] = pt['team']

    # verify embed
    file_embed = admin.get('/api/v1/files/%s?embed=team' % file_id).data
    assert file == file_embed


def test_get_jobdefinition_with_embed_not_valid(admin):
    file = admin.get('/api/v1/files/pname?embed=mdr')
    assert file.status_code == 400


def test_delete_file_by_id(admin, jobstate_id, team_id):
    file = admin.post('/api/v1/files',
                      data={'jobstate_id': jobstate_id, 'team_id': team_id,
                            'content': 'kikoolol', 'name': 'name'})
    file_id = file.data['file']['id']
    file_etag = file.headers.get("ETag")

    url = '/api/v1/files/%s' % file_id

    created_file = admin.get(url)
    assert created_file.status_code == 200

    deleted_file = admin.delete(url, headers={'If-match': file_etag})
    assert deleted_file.status_code == 204

    gfile = admin.get(url)
    assert gfile.status_code == 404
