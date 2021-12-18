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
import mock

from dci.stores.swift import Swift
from dci.common import utils
from dci.api.v1 import tests

import flask

SWIFT = "dci.stores.swift.Swift"


def test_create_tests(user, team_user_id):
    pt = user.post(
        "/api/v1/tests", data={"name": "pname", "team_id": team_user_id}
    ).data
    pt_id = pt["test"]["id"]
    gt = user.get("/api/v1/tests/%s" % pt_id).data
    assert gt["test"]["name"] == "pname"


def test_create_tests_already_exist(user, team_user_id):
    pstatus_code = user.post(
        "/api/v1/tests", data={"name": "pname", "team_id": team_user_id}
    ).status_code
    assert pstatus_code == 201

    pstatus_code = user.post(
        "/api/v1/tests", data={"name": "pname", "team_id": team_user_id}
    ).status_code
    assert pstatus_code == 409


def test_get_all_tests(admin, user):
    test_1 = user.post("/api/v1/tests", data={"name": "pname1"}).data
    test_2 = user.post("/api/v1/tests", data={"name": "pname2"}).data

    db_all_tests = user.get("/api/v1/tests").data

    db_all_tests = db_all_tests["tests"]
    assert len(db_all_tests) == 2
    db_all_tests_ids = set([db_t["id"] for db_t in db_all_tests])

    assert db_all_tests_ids == {test_1["test"]["id"], test_2["test"]["id"]}


def test_get_all_tests_with_pagination(admin, user):
    # create 4 tests and check meta data count
    admin.post("/api/v1/tests", data={"name": "pname1"})
    admin.post("/api/v1/tests", data={"name": "pname2"})
    admin.post("/api/v1/tests", data={"name": "pname3"})
    admin.post("/api/v1/tests", data={"name": "pname4"})

    ts = admin.get("/api/v1/tests").data
    assert ts["_meta"]["count"] == 4

    # verify limit and offset are working well
    ts = user.get("/api/v1/tests?limit=2&offset=0").data
    assert len(ts["tests"]) == 2

    ts = user.get("/api/v1/tests?limit=2&offset=2").data
    assert len(ts["tests"]) == 2

    # if offset is out of bound, the api returns an empty list
    ts = user.get("/api/v1/tests?limit=5&offset=300")
    assert ts.status_code == 200
    assert ts.data["tests"] == []


def test_get_all_tests_with_sort(admin, user, team_user_id, topic_user_id):
    # create 2 tests ordered by created time
    t_1 = admin.post("/api/v1/tests", data={"name": "pname1"}).data["test"]
    t_2 = admin.post("/api/v1/tests", data={"name": "pname2"}).data["test"]

    gts = user.get("/api/v1/tests?sort=created_at").data
    assert gts["tests"][0]["id"] == t_1["id"]
    assert gts["tests"][1]["id"] == t_2["id"]

    # test in reverse order
    gts = user.get("/api/v1/tests?sort=-created_at").data
    assert gts["tests"][0]["id"] == t_2["id"]
    assert gts["tests"][1]["id"] == t_1["id"]


def test_get_test_by_id(admin, team_user_id):
    pt = admin.post("/api/v1/tests", data={"name": "pname"}).data
    pt_id = pt["test"]["id"]

    # get by uuid
    created_t = admin.get("/api/v1/tests/%s" % pt_id)
    assert created_t.status_code == 200

    created_t = created_t.data
    assert created_t["test"]["id"] == pt_id


def test_get_test_not_found(admin):
    result = admin.get("/api/v1/tests/ptdr")
    assert result.status_code == 404


def test_delete_test_by_id(admin, team_user_id):
    pt = admin.post("/api/v1/tests", data={"name": "pname"})
    pt_id = pt.data["test"]["id"]
    assert pt.status_code == 201

    created_t = admin.get("/api/v1/tests/%s" % pt_id)
    assert created_t.status_code == 200
    pt_etag = created_t.data["test"]["etag"]

    deleted_t = admin.delete("/api/v1/tests/%s" % pt_id, headers={"If-match": pt_etag})
    assert deleted_t.status_code == 204

    gt = admin.get("/api/v1/tests/%s" % pt_id)
    assert gt.status_code == 404


def test_delete_test_not_found(admin):
    result = admin.delete(
        "/api/v1/tests/ptdr", headers={"If-match": "eefrwqafeqawfqafeq"}
    )
    assert result.status_code == 404


def test_delete_test_archive_dependencies(admin, job_user_id, team_user_id):
    with mock.patch(SWIFT, spec=Swift) as mock_swift:

        mockito = mock.MagicMock()

        head_result = {
            "etag": utils.gen_etag(),
            "content-type": "stream",
            "content-length": 7,
        }

        mockito.head.return_value = head_result
        mock_swift.return_value = mockito

        test = admin.post("/api/v1/tests", data={"name": "pname"})
        test_id = test.data["test"]["id"]
        assert test.status_code == 201
        test_etag = admin.get("/api/v1/tests/%s" % test_id).data["test"]["etag"]

        file = admin.post(
            "/api/v1/files",
            headers={
                "DCI-NAME": "kikoolol",
                "DCI-JOB-ID": job_user_id,
                "DCI-TEST-ID": test_id,
            },
            data="content",
        )

        file_id = file.data["file"]["id"]
        assert file.status_code == 201

        deleted_test = admin.delete(
            "/api/v1/tests/%s" % test_id, headers={"If-match": test_etag}
        )

        assert deleted_test.status_code == 204

        deleted_file = admin.get("/api/v1/files/%s" % file_id)
        assert deleted_file.status_code == 404


def test_change_test(admin, test_id):
    t = admin.get("/api/v1/tests/" + test_id).data["test"]
    data = {"state": "inactive"}
    r = admin.put(
        "/api/v1/tests/" + test_id, data=data, headers={"If-match": t["etag"]}
    )
    assert r.status_code == 200
    assert r.data["test"]["state"] == "inactive"


def test_change_test_to_invalid_state(admin, test_id):
    t = admin.get("/api/v1/tests/" + test_id).data["test"]
    data = {"state": "kikoolol"}
    r = admin.put(
        "/api/v1/tests/" + test_id, data=data, headers={"If-match": t["etag"]}
    )
    assert r.status_code == 400
    current_test = admin.get("/api/v1/tests/" + test_id)
    assert current_test.status_code == 200
    assert current_test.data["test"]["state"] == "active"


def test_success_update_field_by_field(admin, test_id):
    t = admin.get("/api/v1/tests/%s" % test_id).data["test"]

    admin.put(
        "/api/v1/tests/%s" % test_id,
        data={"state": "inactive"},
        headers={"If-match": t["etag"]},
    )

    t = admin.get("/api/v1/tests/%s" % test_id).data["test"]

    assert t["name"] == "pname"
    assert t["state"] == "inactive"
    assert t["data"] == {}

    admin.put(
        "/api/v1/tests/%s" % test_id,
        data={"name": "pname2"},
        headers={"If-match": t["etag"]},
    )

    t = admin.get("/api/v1/tests/%s" % test_id).data["test"]

    assert t["name"] == "pname2"
    assert t["state"] == "inactive"
    assert t["data"] == {}

    admin.put(
        "/api/v1/tests/%s" % test_id,
        data={"data": {"test": "toto"}},
        headers={"If-match": t["etag"]},
    )

    t = admin.get("/api/v1/tests/%s" % test_id).data["test"]

    assert t["name"] == "pname2"
    assert t["state"] == "inactive"
    assert t["data"] == {"test": "toto"}


def test_get_tests_to_issues(user, topic_user_id, app, engine):
    # associate one test to two issues
    # {'pname1': [{'url': 'http://bugzilla/42', 'id': <id1>},
    #             {'url': 'http://bugzilla/43', 'id': <id2>}]}
    pissue = user.post(
        "/api/v1/issues", data={"url": "http://bugzilla/42", "topic_id": topic_user_id}
    )
    pissue_id1 = pissue.data["issue"]["id"]
    pissue = user.post(
        "/api/v1/issues", data={"url": "http://bugzilla/43", "topic_id": topic_user_id}
    )
    pissue_id2 = pissue.data["issue"]["id"]
    test = user.post("/api/v1/tests", data={"name": "pname1"})
    test_id1 = test.data["test"]["id"]
    user.post("/api/v1/issues/%s/tests" % pissue_id1, data={"test_id": test_id1})
    user.post("/api/v1/issues/%s/tests" % pissue_id2, data={"test_id": test_id1})
    with app.app_context():
        flask.g.db_conn = engine.connect()
        all_tests_to_issues = tests.get_tests_to_issues(topic_user_id)
        assert "pname1" in all_tests_to_issues
        assert len(all_tests_to_issues["pname1"]) == 2
        issues_ids = {str(issue["id"]) for issue in all_tests_to_issues["pname1"]}
        assert issues_ids == {pissue_id1, pissue_id2}
