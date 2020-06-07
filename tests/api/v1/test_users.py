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
import datetime
import uuid

import mock
import pytest

from dci.common.exceptions import DCIException
from dci.common.schemas import (
    check_json_is_valid,
    create_user_schema,
    update_user_schema,
)


def test_create_users(admin, team_id):
    pu = admin.post('/api/v1/users',
                    data={'name': 'pname', 'password': 'ppass',
                          'fullname': 'P Name', 'email': 'pname@example.org'})
    assert pu.status_code == 201
    pu = pu.data
    pu_id = pu['user']['id']
    gu = admin.get('/api/v1/users/%s' % pu_id).data
    assert gu['user']['name'] == 'pname'
    assert gu['user']['timezone'] == 'UTC'


def test_create_user_withouta_team(admin):
    pu = admin.post('/api/v1/users',
                    data={'name': 'pname', 'password': 'ppass',
                          'fullname': 'P Name',
                          'email': 'pname@example.org'})
    assert pu.status_code == 201
    pu = pu.data
    pu_id = pu['user']['id']
    gu = admin.get('/api/v1/users/%s' % pu_id).data
    assert gu['user']['name'] == 'pname'
    assert gu['user']['timezone'] == 'UTC'


def test_create_users_already_exist(admin, team_id):
    pstatus_code = admin.post('/api/v1/users',
                              data={'name': 'pname',
                                    'password': 'ppass',
                                    'fullname': 'P Name',
                                    'email': 'pname@example.org'}).status_code
    assert pstatus_code == 201

    pstatus_code = admin.post('/api/v1/users',
                              data={'name': 'pname',
                                    'password': 'ppass',
                                    'fullname': 'P Name',
                                    'email': 'pname@example.org'}).status_code
    assert pstatus_code == 409


def test_get_teams_of_user(admin, user_id, team_id, team_user_id):
    admin.post('/api/v1/teams/%s/users/%s' % (team_id, user_id),
               data={})
    admin.post('/api/v1/teams/%s/users/%s' % (team_user_id, user_id),
               data={})

    uteams = admin.get('/api/v1/users/%s/teams' % user_id)
    assert uteams.status_code == 200
    assert len(uteams.data['teams']) == 2
    team_ids = {t['id'] for t in uteams.data['teams']}
    assert team_ids == set([team_id, team_user_id])


def test_get_all_users(admin, team_id):
    # TODO(yassine): Currently there is already 3 users created in the DB,
    # this will be fixed later.
    db_users = admin.get('/api/v1/users?sort=created_at').data
    db_users = db_users['users']
    db_users_ids = [db_t['id'] for db_t in db_users]

    user_1 = admin.post('/api/v1/users', data={'name': 'pname1',
                                               'password': 'ppass',
                                               'fullname': 'P Name',
                                               'email': 'pname@example.org'}).data
    user_2 = admin.post('/api/v1/users', data={'name': 'pname2',
                                               'password': 'ppass',
                                               'fullname': 'Q Name',
                                               'email': 'qname@example.org'}).data
    db_users_ids.extend([user_1['user']['id'], user_2['user']['id']])

    db_all_users = admin.get('/api/v1/users?sort=created_at').data
    db_all_users = db_all_users['users']
    db_all_users_ids = [db_t['id'] for db_t in db_all_users]

    assert db_all_users_ids == db_users_ids


def test_where_invalid(admin):
    err = admin.get('/api/v1/users?where=id')

    assert err.status_code == 400
    assert err.data['message'] == "Request malformed"
    assert err.data['payload']['error'] == "where: 'id' is not a 'key value csv'"


def test_get_all_users_with_team(admin):
    # TODO(yassine): Currently there is already 3 users created in the DB,
    # this will be fixed later.
    db_users = admin.get('/api/v1/users?embed=team&where=name:admin').data
    assert 'users' in db_users
    db_users = db_users['users']
    assert 'team' in db_users[0]


def test_get_all_users_with_where(admin, team_id):
    pu = admin.post('/api/v1/users', data={'name': 'pname1',
                                           'password': 'ppass',
                                           'fullname': 'P Name',
                                           'email': 'pname@example.org'}).data
    pu_id = pu['user']['id']

    db_u = admin.get('/api/v1/users?where=id:%s' % pu_id).data
    db_u_id = db_u['users'][0]['id']
    assert db_u_id == pu_id

    db_u = admin.get('/api/v1/users?where=name:pname1').data
    db_u_id = db_u['users'][0]['id']
    assert db_u_id == pu_id


def test_get_all_users_with_pagination(admin, team_id):
    users = admin.get('/api/v1/users').data
    current_users = users['_meta']['count']
    admin.post('/api/v1/users', data={'name': 'pname1',
                                      'password': 'ppass',
                                      'fullname': 'P Name',
                                      'email': 'pname@example.org'})
    admin.post('/api/v1/users', data={'name': 'pname2',
                                      'password': 'ppass',
                                      'fullname': 'Q Name',
                                      'email': 'qname@example.org'})
    admin.post('/api/v1/users', data={'name': 'pname3',
                                      'password': 'ppass',
                                      'fullname': 'R Name',
                                      'email': 'rname@example.org'})
    admin.post('/api/v1/users', data={'name': 'pname4',
                                      'password': 'ppass',
                                      'fullname': 'S Name',
                                      'email': 'sname@example.org'})
    users = admin.get('/api/v1/users').data
    assert users['_meta']['count'] == current_users + 4

    # verify limit and offset are working well
    users = admin.get('/api/v1/users?limit=2&offset=0').data
    assert len(users['users']) == 2

    users = admin.get('/api/v1/users?limit=2&offset=2').data
    assert len(users['users']) == 2

    # if offset is out of bound, the api returns an empty list
    users = admin.get('/api/v1/users?limit=5&offset=300')
    assert users.status_code == 200
    assert users.data['users'] == []


def test_get_all_users_with_sort(admin, team_id):
    # TODO(yassine): Currently there is already 3 users created in the DB,
    # this will be fixed later.
    db_users = admin.get('/api/v1/users?sort=created_at').data
    db_users = db_users['users']

    # create 2 users ordered by created time
    user_1 = admin.post('/api/v1/users',
                        data={'name': 'pname1',
                              'password': 'ppass',
                              'fullname': 'P Name',
                              'email': 'pname@example.org'}).data['user']

    user_2 = admin.post('/api/v1/users',
                        data={'name': 'pname2',
                              'password': 'ppass',
                              'fullname': 'Q Name',
                              'email': 'qname@example.org'}).data['user']

    gusers = admin.get('/api/v1/users?sort=created_at').data
    db_users.extend([user_1, user_2])
    assert gusers['users'] == db_users

    # test in reverse order
    db_users.reverse()
    gusers = admin.get('/api/v1/users?sort=-created_at').data
    assert gusers['users'] == db_users


def test_get_user_by_id(admin, team_id):
    puser = admin.post('/api/v1/users',
                       data={'name': 'pname',
                             'password': 'ppass',
                             'fullname': 'P Name',
                             'email': 'pname@example.org'}).data
    puser_id = puser['user']['id']

    # get by uuid
    created_user = admin.get('/api/v1/users/%s' % puser_id)
    assert created_user.status_code == 200

    created_user = created_user.data
    assert created_user['user']['id'] == puser_id


def test_get_user_not_found(admin):
    result = admin.get('/api/v1/users/%s' % uuid.uuid4())
    assert result.status_code == 404


def test_put_users(admin, team_id):
    pu = admin.post('/api/v1/users', data={'name': 'pname',
                                           'password': 'ppass',
                                           'fullname': 'P Name',
                                           'timezone': 'Europe/Paris',
                                           'email': 'pname@example.org'})
    assert pu.status_code == 201

    pu_etag = pu.headers.get("ETag")

    gu = admin.get('/api/v1/users/%s' % pu.data['user']['id'])
    assert gu.status_code == 200
    assert gu.data['user']['timezone'] == 'Europe/Paris'

    ppu = admin.put('/api/v1/users/%s' % gu.data['user']['id'],
                    data={'name': 'nname'},
                    headers={'If-match': pu_etag})
    assert ppu.status_code == 200
    assert ppu.data['user']['name'] == 'nname'


def test_change_user_state(admin, team_id):
    pu = admin.post('/api/v1/users', data={'name': 'pname',
                                           'password': 'ppass',
                                           'fullname': 'P Name',
                                           'email': 'pname@example.org'})
    assert pu.status_code == 201

    pu_etag = pu.headers.get("ETag")

    gu = admin.get('/api/v1/users/%s' % pu.data['user']['id'])
    assert gu.status_code == 200

    ppu = admin.put('/api/v1/users/%s' % gu.data['user']['id'],
                    data={'state': 'inactive'},
                    headers={'If-match': pu_etag})
    assert ppu.status_code == 200
    assert ppu.data['user']['state'] == 'inactive'


def test_change_user_to_invalid_state(admin, team_id):
    pu = admin.post('/api/v1/users', data={'name': 'pname',
                                           'password': 'ppass',
                                           'fullname': 'P Name',
                                           'email': 'pname@example.org'})
    assert pu.status_code == 201

    pu_etag = pu.headers.get("ETag")

    gu = admin.get('/api/v1/users/%s' % pu.data['user']['id'])
    assert gu.status_code == 200

    ppu = admin.put('/api/v1/users/%s' % gu.data['user']['id'],
                    data={'state': 'kikoolol'},
                    headers={'If-match': pu_etag})
    assert ppu.status_code == 400

    gu = admin.get('/api/v1/users/%s' % pu.data['user']['id'])
    assert gu.status_code == 200
    assert gu.data['user']['state'] == 'active'


def test_delete_user_by_id(admin, team_id):
    pu = admin.post('/api/v1/users',
                    data={'name': 'pname',
                          'password': 'ppass',
                          'fullname': 'P Name',
                          'email': 'pname@example.org'})
    pu_etag = pu.headers.get("ETag")
    pu_id = pu.data['user']['id']
    assert pu.status_code == 201

    created_user = admin.get('/api/v1/users/%s' % pu_id)
    assert created_user.status_code == 200

    deleted_user = admin.delete('/api/v1/users/%s' % pu_id,
                                headers={'If-match': pu_etag})
    assert deleted_user.status_code == 204

    gu = admin.get('/api/v1/users/%s' % pu_id)
    assert gu.status_code == 404


def test_delete_user_with_no_team(admin, user_no_team):
    deleted_user = admin.delete('/api/v1/users/%s' % user_no_team['id'],
                                headers={'If-match': user_no_team['etag']})
    assert deleted_user.status_code == 204


def test_delete_user_not_found(admin):
    result = admin.delete('/api/v1/users/%s' % uuid.uuid4(),
                          headers={'If-match': 'mdr'})
    assert result.status_code == 404


# Tests for the isolation

def test_create_user_as_user(user):
    # simple user cannot add a new user to its team
    pu = user.post('/api/v1/users',
                   data={'name': 'pname',
                         'password': 'ppass',
                         'fullname': 'P Name',
                         'email': 'pname@example.org'})
    assert pu.status_code == 401


def test_get_all_users_as_user(user):
    users = user.get('/api/v1/users')
    assert users.status_code == 401


def test_get_user_as_user(user, admin):
    # admin does not belong to this user's team
    padmin = admin.get('/api/v1/users?where=name:admin')
    padmin = admin.get('/api/v1/users/%s' % padmin.data['users'][0]['id'])

    guser = user.get('/api/v1/users/%s' % padmin.data['user']['id'])
    assert guser.status_code == 401


def get_user(flask_user, name):
    get = flask_user.get('/api/v1/users?where=name:%s' % name)
    get2 = flask_user.get('/api/v1/users/%s' % get.data['users'][0]['id'])
    return get2.data['user'], get2.headers.get("ETag")


def test_admin_can_update_another_user(admin):
    user, etag = get_user(admin, 'user')
    assert admin.put(
        '/api/v1/users/%s' % user['id'],
        data={'name': 'new_name'},
        headers={'If-match': etag}
    ).status_code == 200


def test_user_cant_update_him(admin, user):
    user_data, user_etag = get_user(admin, 'user')

    assert user.put(
        '/api/v1/users/%s' % user_data['id'],
        data={'name': 'new_name'},
        headers={'If-match': user_etag}
    ).status_code == 401


def test_delete_as_user_epm(user, epm, admin):
    puser = epm.get('/api/v1/users?where=name:user')
    puser = epm.get('/api/v1/users/%s' % puser.data['users'][0]['id'])
    user_etag = puser.headers.get("ETag")

    user_delete = user.delete('/api/v1/users/%s' % puser.data['user']['id'],
                              headers={'If-match': user_etag})
    assert user_delete.status_code == 401

    user_delete = epm.delete('/api/v1/users/%s' % puser.data['user']['id'],
                             headers={'If-match': user_etag})
    assert user_delete.status_code == 401

    user_delete = admin.delete('/api/v1/users/%s'
                               % puser.data['user']['id'],
                               headers={'If-match': user_etag})
    assert user_delete.status_code == 204


def test_success_update_field_by_field(admin, team_id):
    user = admin.post('/api/v1/users',
                      data={'name': 'pname', 'password': 'ppass',
                            'fullname': 'P Name', 'email': 'pname@example.org'}).data['user']  # noqa

    t = admin.get('/api/v1/users/%s' % user['id']).data['user']

    admin.put('/api/v1/users/%s' % user['id'],
              data={'state': 'inactive'},
              headers={'If-match': t['etag']})

    t = admin.get('/api/v1/users/%s' % user['id']).data['user']

    assert t['name'] == 'pname'
    assert t['state'] == 'inactive'

    admin.put('/api/v1/users/%s' % user['id'],
              data={'name': 'newuser'},
              headers={'If-match': t['etag']})

    t = admin.get('/api/v1/users/%s' % user['id']).data['user']

    assert t['name'] == 'newuser'
    assert t['state'] == 'inactive'


def test_get_current_user(user):
    user_me = user.get('/api/v1/users/me')
    assert user_me.status_code == 200
    assert user_me.data['user']['name'] == 'user'


def test_update_current_user_password(admin, user):
    user_data, user_etag = get_user(admin, 'user')

    assert user.get('/api/v1/users/me').status_code == 200

    assert user.put(
        '/api/v1/users/me',
        data={'current_password': 'user', 'new_password': 'password'},
        headers={'If-match': user_etag}
    ).status_code == 200

    assert user.get('/api/v1/users/me').status_code == 401

    user_data, user_etag = get_user(admin, 'user')

    assert admin.put(
        '/api/v1/users/%s' % user_data['id'],
        data={'password': 'user'},
        headers={'If-match': user_etag}
    ).status_code == 200

    assert user.get('/api/v1/users/me').status_code == 200


def test_update_current_user_current_password_wrong(admin, user):
    user_data, user_etag = get_user(admin, 'user')

    assert user.get('/api/v1/users/me').status_code == 200

    assert user.put(
        '/api/v1/users/me',
        data={'current_password': 'wrong_password', 'new_password': ''},
        headers={'If-match': user_etag}
    ).status_code == 400

    assert user.get('/api/v1/users/me').status_code == 200


def test_update_current_user_new_password_empty(admin, user):
    user_data, user_etag = get_user(admin, 'user')

    assert user.get('/api/v1/users/me').status_code == 200

    assert user.put(
        '/api/v1/users/me',
        data={'current_password': 'user', 'new_password': ''},
        headers={'If-match': user_etag}
    ).status_code == 200

    assert user.get('/api/v1/users/me').status_code == 200


def test_update_current_user(admin, user):
    user_data, user_etag = get_user(admin, 'user')

    assert user.get('/api/v1/users/me').status_code == 200

    me = user.put(
        '/api/v1/users/me',
        data={'current_password': 'user', 'new_password': '',
              'email': 'new_email@example.org', 'fullname': 'New Name',
              'timezone': 'Europe/Paris'},
        headers={'If-match': user_etag}
    )
    assert me.status_code == 200
    assert me.data['user']['email'] == 'new_email@example.org'
    assert me.data['user']['fullname'] == 'New Name'
    assert me.data['user']['timezone'] == 'Europe/Paris'


@mock.patch('jwt.api_jwt.datetime', spec=datetime.datetime)
def test_update_current_user_sso(m_datetime, user_sso_rh_employee, app,
                                 engine, admin):
    user_sso = user_sso_rh_employee
    m_utcnow = mock.MagicMock()
    m_utcnow.utctimetuple.return_value = datetime.datetime. \
        fromtimestamp(1518653629).timetuple()
    m_datetime.utcnow.return_value = m_utcnow
    with app.app_context():
        assert user_sso.get('/api/v1/users/me').status_code == 200
        user_data, user_etag = get_user(admin, 'dci-rh')

        me = user_sso.put(
            '/api/v1/users/me',
            data={'email': 'new_email@example.org',
                  'fullname': 'New Name',
                  'timezone': 'Europe/Paris'},
            headers={'If-match': user_etag}
        )
        assert me.status_code == 200
        assert me.data['user']['email'] == 'new_email@example.org'
        assert me.data['user']['fullname'] == 'New Name'
        assert me.data['user']['timezone'] == 'Europe/Paris'


def test_get_embed_remotecis(user, remoteci_user_id, user_id):
    r = user.post('/api/v1/remotecis/%s/users' % remoteci_user_id)

    assert r.status_code == 201

    me = user.get('/api/v1/users/me?embed=remotecis').data['user']
    assert me['remotecis'][0]['id'] == remoteci_user_id


def test_success_ensure_put_me_api_secret_is_not_leaked(admin, user):
    """Test to ensure API secret is not leaked during update."""

    user_data, user_etag = get_user(admin, 'user')

    res = user.put(
        '/api/v1/users/me',
        data={'current_password': 'user', 'new_password': 'password'},
        headers={'If-match': user_etag}
    )

    assert res.status_code == 200
    assert 'password' not in res.data['user']


def test_success_ensure_put_api_secret_is_not_leaked(admin, team_id):
    pu = admin.post('/api/v1/users', data={'name': 'pname',
                                           'password': 'ppass',
                                           'fullname': 'P Name',
                                           'timezone': 'Europe/Paris',
                                           'email': 'pname@example.org'})
    pu_etag = pu.headers.get("ETag")
    ppu = admin.put('/api/v1/users/%s' % pu.data['user']['id'],
                    data={'name': 'nname'},
                    headers={'If-match': pu_etag})
    assert ppu.status_code == 200
    assert 'password' not in ppu.data['user']


@pytest.fixture
def user_json():
    return {
        "name": "jdoe",
        "fullname": "John Doe",
        "email": "jdoe@example.org",
    }


def test_create_user_schema(user_json):
    try:
        check_json_is_valid(create_user_schema, user_json)
    except DCIException:
        pytest.fail("create_user_schema is invalid")


def test_create_user_schema_required_value(user_json):
    with pytest.raises(DCIException) as e:
        check_json_is_valid(create_user_schema, {})
    result = e.value
    assert result.status_code == 400
    assert len(result.payload["errors"]) == len(user_json.keys())
    errors = "\n".join(result.payload["errors"])
    for key in user_json.keys():
        assert "'%s' is a required property" % key in errors


def test_create_user_schema_optional_value(user_json):
    try:
        user_json["timezone"] = "Europe/Paris"
        check_json_is_valid(create_user_schema, user_json)
    except DCIException:
        pytest.fail("create_user_schema is invalid")


def test_create_user_schema_no_extra_field(user_json):
    with pytest.raises(DCIException):
        user_json["extra_field"] = "extra field"
        check_json_is_valid(create_user_schema, user_json)


def test_create_user_schema_team_id_type(user_json):
    with pytest.raises(DCIException):
        user_json["team_id"] = "not an uuid"
        check_json_is_valid(create_user_schema, user_json)


def test_create_user_schema_email_format(user_json):
    with pytest.raises(DCIException):
        user_json["email"] = "not an email"
        check_json_is_valid(create_user_schema, user_json)


def test_update_user_schema():
    try:
        check_json_is_valid(update_user_schema, {
            "id": "909b4ad1-1c38-4fc3-9454-57dc6d80b44d",
            "etag": "8407cdbf-04d1-4453-8d35-19e4425c535b",
            "name": "jdoe",
            "fullname": "John Doe",
            "email": "jdoe@example.org",
        })
    except DCIException:
        pytest.fail("update_user_schema is invalid")
