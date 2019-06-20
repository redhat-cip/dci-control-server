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


def test_add_get_users_from_to_team(admin, team_id, user_id):
    # adding two users to the same team
    users = admin.get('/api/v1/teams/%s/users' % team_id)
    current_len = len(users.data['users'])

    pu = admin.post('/api/v1/teams/%s/users/%s' % (team_id, user_id),
                    data={})
    assert pu.status_code == 201

    users = admin.get('/api/v1/teams/%s/users' % team_id)
    assert users.status_code == 200
    print(users.data)
    assert len(users.data['users']) == (current_len + 1)


def test_add_user_to_different_teams(admin, user_id, team_id,
                                     team_user_id, user):
    pu = admin.post('/api/v1/teams/%s/users/%s' % (team_id, user_id),
                    data={})
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
                    data={})
    assert pu.status_code == 201

    du = admin.delete('/api/v1/teams/%s/users/%s' % (team_id, user_id))
    assert du.status_code == 204

    users = admin.get('/api/v1/teams/%s/users' % team_id)
    assert users.status_code == 200
    assert users.data['users'] == []
