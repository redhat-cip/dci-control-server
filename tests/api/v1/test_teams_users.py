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


def test_add_get_users_from_to_team(client_admin, team2_id, user1_id):
    # adding two users to the same team
    users = client_admin.get("/api/v1/teams/%s/users" % team2_id)
    current_len = len(users.data["users"])

    pu = client_admin.post("/api/v1/teams/%s/users/%s" % (team2_id, user1_id), data={})
    assert pu.status_code == 201

    users = client_admin.get("/api/v1/teams/%s/users" % team2_id)
    assert users.status_code == 200
    assert len(users.data["users"]) == (current_len + 1)


def test_add_user_to_different_teams(
    client_admin, user1_id, team1_id, team2_id, client_user1
):
    users = client_admin.get("/api/v1/teams/%s/users" % team1_id)
    assert users.status_code == 200
    assert user1_id in [str(u["id"]) for u in users.data["users"]]

    users = client_admin.get("/api/v1/teams/%s/users" % team2_id)
    assert users.status_code == 200
    assert user1_id not in [str(u["id"]) for u in users.data["users"]]

    pu = client_admin.post("/api/v1/teams/%s/users/%s" % (team2_id, user1_id), data={})
    assert pu.status_code == 201

    users = client_admin.get("/api/v1/teams/%s/users" % team2_id)
    assert users.status_code == 200
    assert user1_id in [str(u["id"]) for u in users.data["users"]]


def test_delete_user_from_team(client_admin, user1_id, team1_id):
    users = client_admin.get("/api/v1/teams/%s/users" % team1_id)
    assert users.status_code == 200
    assert user1_id in [str(u["id"]) for u in users.data["users"]]

    du = client_admin.delete("/api/v1/teams/%s/users/%s" % (team1_id, user1_id))
    assert du.status_code == 204

    users = client_admin.get("/api/v1/teams/%s/users" % team1_id)
    assert users.status_code == 200
    assert user1_id not in [str(u["id"]) for u in users.data["users"]]
