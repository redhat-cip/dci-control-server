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
import uuid
from OpenSSL import crypto


def test_generate_keys(user, team_user_id, remoteci_user_id, cakeys):
    ctype = crypto.FILETYPE_PEM
    rci = user.get('/api/v1/remotecis/%s' % remoteci_user_id).data
    keys = user.put('/api/v1/remotecis/%s/keys' % remoteci_user_id,
                    headers={'If-match': rci['remoteci']['etag']}).data
    tmp_cert = crypto.load_certificate(ctype, keys['keys']['cert'])
    tmp_cert = crypto.dump_certificate(ctype, tmp_cert)
    tmp_key = crypto.load_privatekey(ctype, keys['keys']['key'])
    tmp_key = crypto.dump_privatekey(ctype, tmp_key)
    assert tmp_key.decode('utf-8') == keys['keys']['key']
    assert tmp_cert.decode('utf-8') == keys['keys']['cert']


def test_create_remotecis(user, team_user_id):
    pr = user.post('/api/v1/remotecis',
                   data={'name': 'pname', 'team_id': team_user_id}).data
    pr_id = pr['remoteci']['id']
    gr = user.get('/api/v1/remotecis/%s' % pr_id).data
    assert gr['remoteci']['name'] == 'pname'


def test_create_remotecis_already_exist(user, team_user_id):
    pstatus_code = user.post('/api/v1/remotecis',
                             data={'name': 'pname',
                                   'team_id': team_user_id}).status_code
    assert pstatus_code == 201

    pstatus_code = user.post('/api/v1/remotecis',
                             data={'name': 'pname',
                                   'team_id': team_user_id}).status_code
    assert pstatus_code == 409


def test_create_unique_remoteci_against_teams(user, team_user_id):
    data = {'name': 'foo', 'team_id': team_user_id}
    res = user.post('/api/v1/remotecis', data=data)
    assert res.status_code == 201

    res = user.post('/api/v1/remotecis', data=data)
    assert res.status_code == 409


def test_get_all_remotecis(user, team_user_id):
    remoteci_1 = user.post('/api/v1/remotecis',
                           data={'name': 'pname1',
                                 'team_id': team_user_id}).data
    remoteci_2 = user.post('/api/v1/remotecis',
                           data={'name': 'pname2',
                                 'team_id': team_user_id}).data

    db_all_remotecis = user.get('/api/v1/remotecis?sort=created_at').data
    db_all_remotecis = db_all_remotecis['remotecis']
    db_all_remotecis_ids = [db_t['id'] for db_t in db_all_remotecis]

    assert db_all_remotecis_ids == [remoteci_1['remoteci']['id'],
                                    remoteci_2['remoteci']['id']]


def test_get_all_remotecis_with_where(user, team_user_id):
    pr = user.post('/api/v1/remotecis', data={'name': 'pname1',
                                              'team_id': team_user_id}).data
    pr_id = pr['remoteci']['id']

    db_r = user.get('/api/v1/remotecis?where=id:%s' % pr_id).data
    db_r_id = db_r['remotecis'][0]['id']
    assert db_r_id == pr_id

    db_r = user.get('/api/v1/remotecis?where=name:pname1').data
    db_r_id = db_r['remotecis'][0]['id']
    assert db_r_id == pr_id


def test_where_invalid(admin):
    err = admin.get('/api/v1/remotecis?where=id')

    assert err.status_code == 400
    assert err.data['message'] == "Request malformed"
    assert err.data['payload']['error'] == "where: 'id' is not a 'key value csv'"


def test_get_all_remotecis_with_pagination(user, team_user_id):
    # create 4 remotecis and check meta data count
    user.post('/api/v1/remotecis', data={'name': 'pname1',
                                         'team_id': team_user_id})
    user.post('/api/v1/remotecis', data={'name': 'pname2',
                                         'team_id': team_user_id})
    user.post('/api/v1/remotecis', data={'name': 'pname3',
                                         'team_id': team_user_id})
    user.post('/api/v1/remotecis', data={'name': 'pname4',
                                         'team_id': team_user_id})
    remotecis = user.get('/api/v1/remotecis').data
    assert remotecis['_meta']['count'] == 4

    # verify limit and offset are working well
    remotecis = user.get('/api/v1/remotecis?limit=2&offset=0').data
    assert len(remotecis['remotecis']) == 2

    remotecis = user.get('/api/v1/remotecis?limit=2&offset=2').data
    assert len(remotecis['remotecis']) == 2

    # if offset is out of bound, the api returns an empty list
    remotecis = user.get('/api/v1/remotecis?limit=5&offset=300')
    assert remotecis.status_code == 200
    assert remotecis.data['remotecis'] == []


def test_get_all_remotecis_with_sort(user, team_user_id):
    # create 2 remotecis ordered by created time
    r_1 = user.post('/api/v1/remotecis',
                    data={'name': 'pname1',
                          'team_id': team_user_id}).data['remoteci']
    r_2 = user.post('/api/v1/remotecis',
                    data={'name': 'pname2',
                          'team_id': team_user_id}).data['remoteci']

    grs = user.get('/api/v1/remotecis?sort=created_at').data
    assert grs['remotecis'] == [r_1, r_2]

    # test in reverse order
    grs = user.get('/api/v1/remotecis?sort=-created_at').data
    assert grs['remotecis'] == [r_2, r_1]


def test_get_all_remotecis_embed(admin, team_id):
    team = admin.get('/api/v1/teams/%s' % team_id).data['team']
    # create 2 remotecis
    admin.post('/api/v1/remotecis',
               data={'name': 'pname1', 'team_id': team_id})
    admin.post('/api/v1/remotecis',
               data={'name': 'pname2', 'team_id': team_id})

    # verify embed
    remotecis = admin.get('/api/v1/remotecis?embed=team').data

    for remoteci in remotecis['remotecis']:
        assert remoteci['team'] == team


def test_get_remoteci_by_id(user, team_user_id):
    pr = user.post('/api/v1/remotecis',
                   data={'name': 'pname', 'team_id': team_user_id}).data
    pr_id = pr['remoteci']['id']

    # get by uuid
    created_r = user.get('/api/v1/remotecis/%s' % pr_id)
    assert created_r.status_code == 200

    created_r = created_r.data
    assert created_r['remoteci']['id'] == pr_id


def test_get_remoteci_with_embed(user, team_user_id):
    team = user.get('/api/v1/teams/%s' % team_user_id).data['team']
    premoteci = user.post('/api/v1/remotecis',
                          data={'name': 'pname1',
                                'team_id': team_user_id}).data
    r_id = premoteci['remoteci']['id']

    # verify embed
    db_remoteci = user.get('/api/v1/remotecis/%s?embed=team' % r_id).data
    assert db_remoteci['remoteci']['team'] == team


def test_get_remoteci_not_found(user):
    result = user.get('/api/v1/remotecis/%s' % uuid.uuid4())
    assert result.status_code == 404


def test_get_remoteci_data(user, team_user_id):
    data_data = {'key': 'value'}
    data = {
        'name': 'pname1',
        'team_id': team_user_id,
        'data': data_data
    }

    premoteci = user.post('/api/v1/remotecis', data=data).data

    r_id = premoteci['remoteci']['id']

    r_data = user.get('/api/v1/remotecis/%s/data' % r_id).data
    assert r_data == data_data


def test_get_remoteci_data_specific_keys(user, team_user_id):
    data_key = {'key': 'value'}
    data_key1 = {'key1': 'value1'}

    final_data = {}
    final_data.update(data_key)
    final_data.update(data_key1)
    data = {
        'name': 'pname1',
        'team_id': team_user_id,
        'data': final_data
    }

    premoteci = user.post('/api/v1/remotecis', data=data).data

    r_id = premoteci['remoteci']['id']

    r_data = user.get('/api/v1/remotecis/%s/data' % r_id).data
    assert r_data == final_data

    r_data = user.get('/api/v1/remotecis/%s/data?keys=key' % r_id).data
    assert r_data == data_key

    r_data = user.get('/api/v1/remotecis/%s/data?keys=key1' % r_id).data
    assert r_data == data_key1

    r_data = user.get('/api/v1/remotecis/%s/data?keys=key,key1' % r_id).data
    assert r_data == final_data


def test_put_remotecis(user, team_user_id):
    pr = user.post('/api/v1/remotecis', data={'name': 'pname',
                                              'data': {'a': 1, 'b': 2},
                                              'team_id': team_user_id})
    assert pr.status_code == 201
    assert pr.data['remoteci']['public'] is False

    pr_etag = pr.headers.get("ETag")

    gr = user.get('/api/v1/remotecis/%s' % pr.data['remoteci']['id'])
    assert gr.status_code == 200

    ppr = user.put('/api/v1/remotecis/%s' % gr.data['remoteci']['id'],
                   data={'name': 'nname', 'public': True, 'data': {'c': 3}},
                   headers={'If-match': pr_etag})
    assert ppr.status_code == 200
    assert ppr.data['remoteci']['name'] == 'nname'
    assert ppr.data['remoteci']['public'] is True
    assert set(ppr.data['remoteci']['data']) == set(['c'])


def test_delete_remoteci_by_id(user, team_user_id):
    pr = user.post('/api/v1/remotecis',
                   data={'name': 'pname', 'team_id': team_user_id})
    pr_etag = pr.headers.get("ETag")
    pr_id = pr.data['remoteci']['id']
    assert pr.status_code == 201

    created_r = user.get('/api/v1/remotecis/%s' % pr_id)
    assert created_r.status_code == 200

    deleted_r = user.delete('/api/v1/remotecis/%s' % pr_id,
                            headers={'If-match': pr_etag})
    assert deleted_r.status_code == 204

    gr = user.get('/api/v1/remotecis/%s' % pr_id)
    assert gr.status_code == 404


def test_delete_remoteci_not_found(user):
    result = user.delete('/api/v1/remotecis/%s' % uuid.uuid4(),
                         headers={'If-match': 'mdr'})
    assert result.status_code == 404


def test_delete_remoteci_archive_dependencies(user, team_user_id,
                                              remoteci_user_id,
                                              topic_user_id,
                                              components_user_ids,
                                              remoteci_context):
    data = {'topic_id': topic_user_id,
            'remoteci_id': remoteci_user_id,
            'components_ids': components_user_ids}
    job = remoteci_context.post('/api/v1/jobs/schedule', data=data)
    assert job.status_code == 201

    url = '/api/v1/remotecis/%s' % remoteci_user_id
    rci = user.get(url)
    etag = rci.data['remoteci']['etag']
    assert rci.status_code == 200

    deleted_rci = user.delete(url, headers={'If-match': etag})
    assert deleted_rci.status_code == 204

    url = '/api/v1/jobs/%s' % job.data['job']['id']
    job = user.get(url)
    assert job.status_code == 404


# Tests for the isolation

def test_create_remoteci_as_user(user, team_user_id, team_id):
    remoteci = user.post('/api/v1/remotecis',
                         data={'name': 'rname', 'team_id': team_id})
    assert remoteci.status_code == 401

    remoteci = user.post('/api/v1/remotecis',
                         data={'name': 'rname', 'team_id': team_user_id})
    assert remoteci.status_code == 201


@pytest.mark.usefixtures('remoteci_id', 'remoteci_user_id')
def test_get_all_remotecis_as_user(user, team_user_id):
    remotecis = user.get('/api/v1/remotecis')
    assert remotecis.status_code == 200
    assert remotecis.data['_meta']['count'] == 1
    for remoteci in remotecis.data['remotecis']:
        assert remoteci['team_id'] == team_user_id


def test_get_remoteci_as_user(user, team_user_id, remoteci_id):
    remoteci = user.get('/api/v1/remotecis/%s' % remoteci_id)
    assert remoteci.status_code == 404

    remoteci = user.post('/api/v1/remotecis',
                         data={'name': 'rname', 'team_id': team_user_id})
    remoteci = user.get('/api/v1/remotecis/%s'
                        % remoteci.data['remoteci']['id'])
    assert remoteci.status_code == 200


def test_put_remoteci_as_user(user, team_user_id, remoteci_id, admin):
    remoteci = user.post('/api/v1/remotecis',
                         data={'name': 'rname', 'team_id': team_user_id})
    remoteci = user.get('/api/v1/remotecis/%s'
                        % remoteci.data['remoteci']['id'])
    remoteci_etag = remoteci.headers.get("ETag")

    remoteci_put = user.put('/api/v1/remotecis/%s'
                            % remoteci.data['remoteci']['id'],
                            data={'name': 'nname'},
                            headers={'If-match': remoteci_etag})
    assert remoteci_put.status_code == 200

    remoteci = user.get('/api/v1/remotecis/%s'
                        % remoteci.data['remoteci']['id']).data['remoteci']
    assert remoteci['name'] == 'nname'

    remoteci = admin.get('/api/v1/remotecis/%s' % remoteci_id)
    remoteci_etag = remoteci.headers.get("ETag")
    remoteci_put = user.put('/api/v1/remotecis/%s' % remoteci_id,
                            data={'name': 'nname'},
                            headers={'If-match': remoteci_etag})
    assert remoteci_put.status_code == 401


def test_delete_remoteci_as_user(user, team_user_id, admin, remoteci_id):
    remoteci = user.post('/api/v1/remotecis',
                         data={'name': 'rname', 'team_id': team_user_id})
    remoteci = user.get('/api/v1/remotecis/%s'
                        % remoteci.data['remoteci']['id'])
    remoteci_etag = remoteci.headers.get("ETag")

    remoteci_delete = user.delete('/api/v1/remotecis/%s'
                                  % remoteci.data['remoteci']['id'],
                                  headers={'If-match': remoteci_etag})
    assert remoteci_delete.status_code == 204

    remoteci = admin.get('/api/v1/remotecis/%s' % remoteci_id)
    remoteci_etag = remoteci.headers.get("ETag")
    remoteci_delete = user.delete('/api/v1/remotecis/%s' % remoteci_id,
                                  headers={'If-match': remoteci_etag})
    assert remoteci_delete.status_code == 401


def test_change_remoteci_state(admin, remoteci_id):
    t = admin.get('/api/v1/remotecis/' + remoteci_id).data['remoteci']
    data = {'state': 'inactive'}
    r = admin.put('/api/v1/remotecis/' + remoteci_id,
                  data=data,
                  headers={'If-match': t['etag']})
    assert r.status_code == 200
    assert r.data['remoteci']['state'] == 'inactive'


def test_change_remoteci_to_invalid_state(admin, remoteci_id):
    t = admin.get('/api/v1/remotecis/' + remoteci_id).data['remoteci']
    data = {'state': 'kikoolol'}
    r = admin.put('/api/v1/remotecis/' + remoteci_id,
                  data=data,
                  headers={'If-match': t['etag']})
    assert r.status_code == 400
    current_remoteci = admin.get('/api/v1/remotecis/' + remoteci_id)
    assert current_remoteci.status_code == 200
    assert current_remoteci.data['remoteci']['state'] == 'active'


def test_success_attach_user_to_remoteci_in_team_as_admin(admin, user, user_id,
                                                          remoteci_user_id):

    r = user.post('/api/v1/remotecis/%s/users' % remoteci_user_id)

    assert r.status_code == 201


def test_success_attach_po_to_partner_remoteci(admin, remoteci_user_id, epm):

    r = epm.post('/api/v1/remotecis/%s/users' % remoteci_user_id)

    assert r.status_code == 201


def test_success_attach_myself_to_remoteci_in_team(user, user_id,
                                                   remoteci_user_id):

    r = user.post('/api/v1/remotecis/%s/users' % remoteci_user_id)

    assert r.status_code == 201


def test_failure_attach_myself_to_remoteci_not_in_team(user, user_id,
                                                       remoteci_id):

    r = user.post('/api/v1/remotecis/%s/users' % remoteci_id)

    assert r.status_code == 401


def test_success_detach_myself_from_remoteci_in_team(user, user_id,
                                                     remoteci_user_id):

    r = user.post('/api/v1/remotecis/%s/users' % remoteci_user_id)

    assert r.status_code == 201

    r = user.delete('/api/v1/remotecis/%s/users/%s' % (remoteci_user_id,
                                                       user_id))
    assert r.status_code == 204


def test_get_subscribed_remotecis(remoteci_user_id, user, user_id):
    response = user.get("/api/v1/users/%s/remotecis" % user_id)
    assert response.data["remotecis"] == []
    user.post("/api/v1/remotecis/%s/users" % remoteci_user_id)
    response = user.get("/api/v1/users/%s/remotecis" % user_id)
    assert response.data["remotecis"][0]["id"] == remoteci_user_id


def test_remove_subscription_to_remoteci(remoteci_user_id, user, user_id):
    response = user.get("/api/v1/users/%s/remotecis" % user_id)
    assert response.data["remotecis"] == []
    user.post("/api/v1/remotecis/%s/users" % remoteci_user_id)
    response = user.get("/api/v1/users/%s/remotecis" % user_id)
    assert response.data["remotecis"][0]["id"] == remoteci_user_id
    response = user.delete(
        "/api/v1/remotecis/%s/users/%s" % (remoteci_user_id, user_id)
    )
    assert response.status_code == 204
    response = user.get("/api/v1/users/%s/remotecis" % user_id)
    assert response.data["remotecis"] == []


def test_remove_subscription_to_remoteci_even_if_remoteci_doesnt_exists(
    user, user_id, team_user_id
):
    remoteci_data = {"name": "to delete", "team_id": team_user_id}
    response = user.post("/api/v1/remotecis", data=remoteci_data)
    remoteci = response.data["remoteci"]
    user.post("/api/v1/remotecis/%s/users" % remoteci["id"])
    response = user.get("/api/v1/users/%s/remotecis" % user_id)
    assert response.data["remotecis"][0]["id"] == remoteci["id"]
    response = user.delete(
        "/api/v1/remotecis/%s" % remoteci["id"], headers={"If-match": remoteci["etag"]},
    )
    assert response.status_code == 204
    response = user.delete("/api/v1/remotecis/%s/users/%s" % (remoteci["id"], user_id))
    assert response.status_code == 204
    response = user.get("/api/v1/users/%s/remotecis" % user_id)
    assert response.data["remotecis"] == []


def test_success_ensure_put_api_secret_is_not_leaked(user, team_user_id):
    """Test to ensure API secret is not leaked during update."""

    pr = user.post('/api/v1/remotecis', data={'name': 'pname',
                                              'data': {'a': 1, 'b': 2},
                                              'team_id': team_user_id})
    pr_etag = pr.headers.get("ETag")
    ppr = user.put('/api/v1/remotecis/%s' % pr.data['remoteci']['id'],
                   data={'name': 'nname', 'public': True, 'data': {'c': 3}},
                   headers={'If-match': pr_etag})
    assert ppr.status_code == 200
    assert 'api_secret' not in ppr.data['remoteci']
