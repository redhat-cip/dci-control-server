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
import uuid


def test_create_teams(admin, team_admin_id):
    pt = admin.post('/api/v1/teams',
                    data={'name': 'pname'}).data
    pt_id = pt['team']['id']
    gt = admin.get('/api/v1/teams/%s' % pt_id).data
    assert gt['team']['name'] == 'pname'
    assert gt['team']['parent_id'] == team_admin_id

    pt = admin.post('/api/v1/teams',
                    data={'name': 'pname2',
                          'parent_id': team_admin_id}).data
    pt_id = pt['team']['id']
    gt = admin.get('/api/v1/teams/%s' % pt_id).data
    assert gt['team']['name'] == 'pname2'
    assert gt['team']['parent_id'] == team_admin_id


def test_create_teams_already_exist(admin):
    pstatus_code = admin.post('/api/v1/teams',
                              data={'name': 'pname'}).status_code
    assert pstatus_code == 201

    pstatus_code = admin.post('/api/v1/teams',
                              data={'name': 'pname'}).status_code
    assert pstatus_code == 409


def test_get_all_teams(admin):
    # TODO(yassine): Currently there is already 3 teams created in the DB,
    # this will be fixed later.
    db_teams = admin.get('/api/v1/teams?sort=created_at').data
    db_teams = db_teams['teams']
    db_teams_ids = [db_t['id'] for db_t in db_teams]

    test_1 = admin.post('/api/v1/teams', data={'name': 'pname1'}).data
    test_2 = admin.post('/api/v1/teams', data={'name': 'pname2'}).data
    db_teams_ids.extend([test_1['team']['id'], test_2['team']['id']])

    db_get_all_teams = admin.get('/api/v1/teams?sort=created_at').data
    db_get_all_teams = db_get_all_teams['teams']
    db_get_all_teams_ids = [db_t['id'] for db_t in db_get_all_teams]

    assert db_get_all_teams_ids == db_teams_ids


def test_get_all_teams_with_where(admin):
    pt = admin.post('/api/v1/teams', data={'name': 'pname1'}).data
    pt_id = pt['team']['id']

    db_t = admin.get('/api/v1/teams?where=id:%s' % pt_id).data
    db_t_id = db_t['teams'][0]['id']
    assert db_t_id == pt_id

    db_t = admin.get('/api/v1/teams?where=name:pname1').data
    db_t_id = db_t['teams'][0]['id']
    assert db_t_id == pt_id


def test_where_invalid(admin):
    err = admin.get('/api/v1/teams?where=id')

    assert err.status_code == 400
    assert err.data['message'] == "Request malformed"
    assert err.data['payload']['error'] == "where: 'id' is not a 'key value csv'"


def test_get_all_teams_with_pagination(admin):
    ts = admin.get('/api/v1/teams').data
    current_teams = ts['_meta']['count']
    # create 4 components types and check meta data count
    admin.post('/api/v1/teams', data={'name': 'pname1'})
    admin.post('/api/v1/teams', data={'name': 'pname2'})
    admin.post('/api/v1/teams', data={'name': 'pname3'})
    admin.post('/api/v1/teams', data={'name': 'pname4'})
    ts = admin.get('/api/v1/teams').data
    assert ts['_meta']['count'] == current_teams + 4

    # verify limit and offset are working well
    ts = admin.get('/api/v1/teams?limit=2&offset=0').data
    assert len(ts['teams']) == 2

    ts = admin.get('/api/v1/teams?limit=2&offset=2').data
    assert len(ts['teams']) == 2

    # if offset is out of bound, the api returns an empty list
    ts = admin.get('/api/v1/teams?limit=5&offset=300')
    assert ts.status_code == 200
    assert ts.data['teams'] == []


def test_get_all_teams_with_sort(admin):
    # TODO(yassine): Currently there is already 3 teams created in the DB,
    # this will be fixed later.
    db_teams = admin.get('/api/v1/teams?sort=created_at').data
    db_teams = db_teams['teams']

    # create 2 teams ordered by created time
    t_1 = admin.post('/api/v1/teams',
                     data={'name': 'pname1'}).data['team']
    t_2 = admin.post('/api/v1/teams',
                     data={'name': 'pname2'}).data['team']

    gts = admin.get('/api/v1/teams?sort=created_at').data
    db_teams.extend([t_1, t_2])
    assert gts['teams'] == db_teams

    # test in reverse order
    db_teams.reverse()
    gts = admin.get('/api/v1/teams?sort=-created_at').data
    assert gts['teams'] == db_teams


def test_get_all_teams_with_embed(admin, topic_user_id):
    db_teams = admin.get('/api/v1/teams?embed=topics&where=name:user').data
    assert db_teams['teams'][0]['topics'][0]['id'] == topic_user_id


def test_get_team_by_id(admin):
    pt = admin.post('/api/v1/teams',
                    data={'name': 'pname'}).data
    pt_id = pt['team']['id']

    # get by uuid
    created_t = admin.get('/api/v1/teams/%s' % pt_id)
    assert created_t.status_code == 200

    created_t = created_t.data
    assert created_t['team']['id'] == pt_id


def test_get_team_not_found(admin):
    result = admin.get('/api/v1/teams/%s' % uuid.uuid4())
    assert result.status_code == 404


def test_put_teams(admin):
    pt = admin.post('/api/v1/teams', data={'name': 'pname'})
    assert pt.status_code == 201

    pt_etag = pt.headers.get("ETag")

    gt = admin.get('/api/v1/teams/%s' % pt.data['team']['id'])
    assert gt.status_code == 200

    ppt = admin.put('/api/v1/teams/%s' % gt.data['team']['id'],
                    data={'name': 'nname'},
                    headers={'If-match': pt_etag})
    assert ppt.status_code == 200
    assert ppt.data['team']['name'] == 'nname'


def test_put_team_external_flag(user, admin, product_owner, team_product_id):
    cteam = admin.post('/api/v1/teams', data={'name': 'pname',
                                              'parent_id': team_product_id})
    cteam_id = cteam.data['team']['id']

    cteam = product_owner.get('/api/v1/teams/%s' % cteam_id)
    assert cteam.status_code == 200
    cteam_etag = cteam.headers.get('ETag')

    cteam_put = user.put('/api/v1/teams/%s' % cteam_id,
                         data={'external': False},
                         headers={'If-match': cteam_etag})
    assert cteam_put.status_code == 401

    cteam_put = product_owner.put('/api/v1/teams/%s' % cteam_id,
                                  data={'external': False},
                                  headers={'If-match': cteam_etag})
    assert cteam_put.status_code == 200
    assert cteam_put.data['team']['external'] is False


def test_delete_team_by_id(admin):
    pt = admin.post('/api/v1/teams',
                    data={'name': 'pname'})
    pt_etag = pt.headers.get("ETag")
    pt_id = pt.data['team']['id']
    assert pt.status_code == 201

    created_t = admin.get('/api/v1/teams/%s' % pt_id)
    assert created_t.status_code == 200

    deleted_t = admin.delete('/api/v1/teams/%s' % pt_id,
                             headers={'If-match': pt_etag})
    assert deleted_t.status_code == 204

    gt = admin.get('/api/v1/teams/%s' % pt_id)
    assert gt.status_code == 404


def test_delete_team_not_found(admin):
    result = admin.delete('/api/v1/teams/%s' % uuid.uuid4(),
                          headers={'If-match': 'mdr'})
    assert result.status_code == 404


def test_delete_team_archive_dependencies(admin, remoteci_context, product,
                                          team_user_id):
    team_user = admin.get('/api/v1/teams/%s' % team_user_id).data['team']
    team_user_etag = team_user['etag']

    user = admin.post('/api/v1/users',
                      data={'name': 'pname', 'password': 'ppass',
                            'fullname': 'P Name',
                            'email': 'pname@example.org',
                            'team_id': team_user_id})
    user_id = user.data['user']['id']
    assert user.status_code == 201

    remoteci = admin.post('/api/v1/remotecis',
                          data={'name': 'pname', 'team_id': team_user_id})
    remoteci_id = remoteci.data['remoteci']['id']
    assert remoteci.status_code == 201

    topic = admin.post('/api/v1/topics',
                       data={'name': 'topic_name',
                             'product_id': product['id'],
                             'component_types': ['type1', 'type2']})
    topic_id = topic.data['topic']['id']
    assert topic.status_code == 201

    data = {
        'name': 'pname',
        'type': 'gerrit_review',
        'url': 'http://example.com/',
        'topic_id': topic_id,
        'export_control': True,
        'state': 'active'}
    component = admin.post('/api/v1/components', data=data)
    component_id = component.data['component']['id']
    assert component.status_code == 201

    data = {'team_id': team_user_id,
            'comment': 'kikoolol',
            'components': [component_id]}
    job = remoteci_context.post('/api/v1/jobs', data=data)
    job_id = job.data['job']['id']
    assert job.status_code == 201

    deleted_team = admin.delete('/api/v1/teams/%s' % team_user_id,
                                headers={'If-match': team_user_etag})
    assert deleted_team.status_code == 204

    deleted_user = admin.get('/api/v1/users/%s' % user_id)
    assert deleted_user.status_code == 404

    deleted_remoteci = admin.get('/api/v1/remotecis/%s' % remoteci_id)
    assert deleted_remoteci.status_code == 404

    deleted_job = admin.get('/api/v1/jobs/%s' % job_id)
    assert deleted_job.status_code == 404


# Tests for the isolation

def test_create_team_as_user(user):
    team = user.post('/api/v1/teams',
                     data={'name': 'pname'})
    assert team.status_code == 401


def test_get_all_teams_as_user(user):
    teams = user.get('/api/v1/teams')
    assert teams.status_code == 200


def test_get_teams_as_user(user, team_user_id, team_admin_id):
    team = user.get('/api/v1/teams/%s' % team_admin_id)
    assert team.status_code == 401

    team = user.get('/api/v1/teams/%s' % team_user_id)
    assert team.status_code == 200

    teams = user.get('/api/v1/teams')
    assert teams.status_code == 200
    assert len(teams.data['teams']) == 1


def test_change_team_state(admin, team_id):
    t = admin.get('/api/v1/teams/' + team_id).data['team']
    data = {'state': 'inactive'}
    r = admin.put('/api/v1/teams/' + team_id,
                  data=data,
                  headers={'If-match': t['etag']})
    assert r.status_code == 200
    assert r.data['team']['state'] == 'inactive'


def test_change_team_to_invalid_state(admin, team_id):
    t = admin.get('/api/v1/teams/' + team_id).data['team']
    data = {'state': 'kikoolol'}
    r = admin.put('/api/v1/teams/' + team_id,
                  data=data,
                  headers={'If-match': t['etag']})
    assert r.status_code == 400
    current_team = admin.get('/api/v1/teams/' + team_id)
    assert current_team.status_code == 200
    assert current_team.data['team']['state'] == 'active'


# Only super admin can delete a team
def test_delete_as_admin(user, team_user_id, admin):
    team = user.get('/api/v1/teams/%s' % team_user_id)
    team_etag = team.headers.get("ETag")

    team_delete = user.delete('/api/v1/teams/%s' % team_user_id,
                              headers={'If-match': team_etag})
    assert team_delete.status_code == 401

    team_delete = admin.delete('/api/v1/teams/%s' % team_user_id,
                               headers={'If-match': team_etag})
    assert team_delete.status_code == 204


def test_success_update_field_by_field(admin, team_id):
    t = admin.get('/api/v1/teams/%s' % team_id).data['team']

    admin.put('/api/v1/teams/%s' % team_id,
              data={'state': 'inactive'},
              headers={'If-match': t['etag']})

    t = admin.get('/api/v1/teams/%s' % team_id).data['team']

    assert t['name'] == 'pname'
    assert t['state'] == 'inactive'
    assert t['country'] is None

    admin.put('/api/v1/teams/%s' % team_id,
              data={'country': 'FR'},
              headers={'If-match': t['etag']})

    t = admin.get('/api/v1/teams/%s' % team_id).data['team']

    assert t['name'] == 'pname'
    assert t['state'] == 'inactive'
    assert t['country'] == 'FR'
