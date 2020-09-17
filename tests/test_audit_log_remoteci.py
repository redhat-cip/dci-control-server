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

from dci.common.audits import log_action
import flask


def test_log_action_with_remoteci_id(engine, admin, remoteci_id, team_id):
    class Flask_g_mock(object):
        def __init__(self):
            self.db_conn = engine

    _g = flask.g
    flask.g = Flask_g_mock()
    log_action(remoteci_id, "some_action")
    flask.g = _g

    gaudits = admin.get("/api/v1/audits")
    assert gaudits.status_code == 200
    assert gaudits.data["audits"][0]["user_id"] == remoteci_id
