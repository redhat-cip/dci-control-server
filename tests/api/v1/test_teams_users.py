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

from dci.api.v1.teams_users import serialize_users, serialize_teams


def test_serialize_users():
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

    new_users = serialize_users(users)
    assert new_users[0] == users_expected[0]


def test_serialize_teams():
    teams = [{"country": None,
              "created_at": "2019-04-11T08:32:16.619884",
              "etag": "07db9594266d1569813441163a546331",
              "external": True,
              "id": "36f4c548-162a-4b65-bce4-76613398bf5c",
              "name": "RHEL",
              "parent_id": "4b48ae10-1b9e-42e2-a5d3-113ab365d6c4",
              "state": "active",
              "updated_at": "2019-04-11T08:32:16.619884",
              "users": {
                  "teams_roles_role": "USER",
                  "teams_roles_team_id": "36f4c548-162a-4b65-bce4-76613398bf5c",  # noqa
                  "teams_roles_user_id": "bc7949a2-c821-4e3e-930e-d0fbfacb0e1f"
              }}]

    teams_expected = [{
        "country": None,
        "created_at": "2019-04-11T08:32:16.619884",
        "etag": "07db9594266d1569813441163a546331",
        "external": True,
        "id": "36f4c548-162a-4b65-bce4-76613398bf5c",
        "name": "RHEL",
        "parent_id": "4b48ae10-1b9e-42e2-a5d3-113ab365d6c4",
        "role": "USER",
        "state": "active",
        "updated_at": "2019-04-11T08:32:16.619884"
    }]

    new_teams = serialize_teams(teams)
    assert new_teams[0] == teams_expected[0]


def test_add_get_users_from_to_team(admin, team_id, user_id):
    # adding two users to the same team
    users = admin.get('/api/v1/teams/%s/users' % team_id)
    current_len = len(users.data['users'])

    pu = admin.post('/api/v1/teams/%s/users/%s' % (team_id, user_id),
                    data={'role': 'USER'})
    assert pu.status_code == 201

    users = admin.get('/api/v1/teams/%s/users' % team_id)
    assert users.status_code == 200
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


def test_get_teams_of_user(admin, user_id):
    user_teams = admin.get('/api/v1/users/%s/teams' % user_id).data
    user_teams_names = {t['name'] for t in user_teams['teams']}
    assert user_teams_names == {'user', 'user_bis'}
    for t in user_teams['teams']:
        assert t['role'] == 'USER'
    assert user_teams['child_teams'] == []


def test_get_teams_of_user_as_product_owner(user_id, product_owner):
    user_teams = product_owner.get('/api/v1/users/%s/teams' % user_id).data
    user_teams_names = {t['name'] for t in user_teams['teams']}
    # product owner will not see the 'user_bis' team because it's not in
    # it's child team
    assert user_teams_names == {'user'}
    for t in user_teams['teams']:
        assert t['role'] == 'USER'
    assert user_teams['child_teams'] == []


def test_get_teams_of_product_owner(admin, product_owner_id):
    user_teams = admin.get('/api/v1/users/%s/teams' % product_owner_id).data
    print(user_teams['teams'])
    print(user_teams['child_teams'])
    user_teams_names = {t['name'] for t in user_teams['teams']}
    assert user_teams_names == {'product'}
    user_child_teams_names = {t['name'] for t in user_teams['child_teams']}
    assert user_child_teams_names == {'user'}


def test_delete_user_from_team(admin, user_id, team_id):
    pu = admin.post('/api/v1/teams/%s/users/%s' % (team_id, user_id),
                    data={'role': 'USER'})
    assert pu.status_code == 201

    du = admin.delete('/api/v1/teams/%s/users/%s' % (team_id, user_id))
    assert du.status_code == 204

    users = admin.get('/api/v1/teams/%s/users' % team_id)
    assert users.status_code == 200
    assert users.data['users'] == []
