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


def test_audits(admin):
    gaudits = admin.get("/api/v1/audits").data
    assert len(gaudits["audits"]) == 0

    pt = admin.post("/api/v1/teams", data={"name": "kikoolol"})
    assert pt.status_code == 201

    gaudits = admin.get("/api/v1/audits").data
    assert len(gaudits["audits"]) == 1
    fields = gaudits["audits"][0]
    assert "logs_action" not in fields
    assert "logs_created_at" not in fields
    assert "logs_id" not in fields
    assert "logs_team_id" not in fields
    assert "logs_user_id" not in fields
    assert "created_at" in fields
    assert "id" in fields
    assert "user_id" in fields
    assert fields["action"] == "create_teams"


def test_audits_acls(admin, user, team_admin_id):
    pt = admin.post("/api/v1/teams", data={"name": "kikoolol"})
    assert pt.status_code == 201

    gaudits = admin.get("/api/v1/audits")
    assert gaudits.status_code == 200

    gaudits = user.get("/api/v1/audits")
    assert gaudits.status_code == 401
