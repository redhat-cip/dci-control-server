# -*- coding: utf-8 -*-
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

from dci.api.v1.teams_users import serialize


def test_serialize():
    users = [{'timezone': 'UTC',
              'teams_roles_role': 'USER',
              'teams_roles_user_id': '0fbaf062-b040-42d0-bc44-8550a92532f0',
              'created_at': '2019-04-03T13:11:54.740416',
              'etag': 'ea79da01e365dd23fe3d8fb628b12c75',
              'fullname': 'User',
              'id': '0fbaf062-b040-42d0-bc44-8550a92532f0',
              'teams_roles_team_id': '2f319d35-f0d7-4e3b-a906-bfff9158918c',
              'updated_at': '2019-04-03T13:11:54.740424',
              'email': 'user@example.org',
              'name': 'user',
              'state': 'active',
              'sso_username': 'user'}]

    users_expected = [{'timezone': 'UTC',
                       'role': 'USER',
                       'created_at': '2019-04-03T13:11:54.740416',
                       'etag': 'ea79da01e365dd23fe3d8fb628b12c75',
                       'fullname': 'User',
                       'id': '0fbaf062-b040-42d0-bc44-8550a92532f0',
                       'updated_at': '2019-04-03T13:11:54.740424',
                       'email': 'user@example.org',
                       'name': 'user',
                       'state': 'active',
                       'sso_username': 'user'}]

    new_users = serialize(users)
    import pprint
    pprint.pprint(new_users[0])
    pprint.pprint(users_expected[0])
    assert new_users[0] == users_expected[0]


def test_add_get_users_from_to_team(admin, team_id, user_id):
    # adding two users to the same team
    users = admin.get('/api/v1/teams/%s/users' % team_id)
    current_len = len(users.data['users'])

    pu = admin.post('/api/v1/teams/%s/users/%s' % (team_id, user_id),
                    data={'role': 'USER'})
    assert pu.status_code == 201

    users = admin.get('/api/v1/teams/%s/users' % team_id)
    assert users.status_code == 200
    print(users.data)
    assert len(users.data['users']) == (current_len + 1)
    for u in users.data['users']:
        assert 'role' in u


def test_add_user_to_different_teams(admin, user_id, team_id,
                                     team_user_id, user):
    pu = admin.post('/api/v1/teams/%s/users/%s' % (team_id, user_id),
                    data={'role': 'USER'})
    assert pu.status_code == 201

    users = admin.get('/api/v1/teams/%s/users' % team_id)
    assert users.status_code == 200
    assert users.data['users'][0]['id'] == user_id

    users = admin.get('/api/v1/teams/%s/users' % team_user_id)
    assert users.status_code == 200
    assert (users.data['users'][0]['id'] == user_id or
            users.data['users'][1]['id'] == user_id)


def test_delete_user_from_team(admin, user_id, team_id):
    pu = admin.post('/api/v1/teams/%s/users/%s' % (team_id, user_id),
                    data={'role': 'USER'})
    assert pu.status_code == 201

    du = admin.delete('/api/v1/teams/%s/users/%s' % (team_id, user_id))
    assert du.status_code == 204

    users = admin.get('/api/v1/teams/%s/users' % team_id)
    assert users.status_code == 200
    assert users.data['users'] == []
