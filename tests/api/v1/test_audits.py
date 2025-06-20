# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2017 Red Hat, Inc
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
from mock import ANY


def test_create_team_store_a_log_in_audit_table(client_admin, client_epm, epm):
    assert len(client_admin.get("/api/v1/audits").data["audits"]) == 0
    client_epm.post("/api/v1/teams", data={"name": "partner"}).data["team"]
    audits = client_admin.get("/api/v1/audits").data["audits"]
    assert len(audits) == 1
    assert audits[0] == {
        "id": ANY,
        "user_id": epm["id"],
        "action": "create_teams",
        "created_at": ANY,
    }


def test_audits_acls(client_admin, client_user1):
    pt = client_admin.post("/api/v1/teams", data={"name": "kikoolol"})
    assert pt.status_code == 201

    gaudits = client_admin.get("/api/v1/audits")
    assert gaudits.status_code == 200

    gaudits = client_user1.get("/api/v1/audits")
    assert gaudits.status_code == 401
