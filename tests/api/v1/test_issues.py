# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Red Hat, Inc
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
import requests

GITHUB_TRACKER = "dci.trackers.github.requests"
BUGZILLA_TRACKER = "dci.trackers.bugzilla.requests"


def test_attach_issue_to_job(user, job_user_id, topic_user_id):
    with mock.patch(GITHUB_TRACKER, spec=requests) as mock_github_request:

        mock_github_result = mock.Mock()
        mock_github_request.get.return_value = mock_github_result

        mock_github_result.status_code = 200
        mock_github_result.json.return_value = {
            "number": 1,  # issue_id
            "title": "Create a GET handler for /componenttype/<ct_name>",
            "user": {"login": "Spredzy"},  # reporter
            "assignee": None,
            "state": "closed",  # status
            "product": "redhat-cip",
            "component": "dci-control-server",
            "created_at": "2015-12-09T09:29:26Z",
            "updated_at": "2015-12-18T15:19:41Z",
            "closed_at": "2015-12-18T15:19:41Z",
        }

        data = {
            "url": "https://github.com/redhat-cip/dci-control-server/issues/1",
            "topic_id": topic_user_id,
        }
        issue = user.post("/api/v1/jobs/%s/issues" % job_user_id, data=data).data
        result = user.get("/api/v1/jobs/%s/issues" % job_user_id).data
        assert result["issues"][0]["id"] == issue["issue"]["id"]
        assert result["issues"][0]["url"] == data["url"]


def test_attach_issue_to_component(admin, user, topic_user_id):
    with mock.patch(GITHUB_TRACKER, spec=requests) as mock_github_request:
        data = {
            "name": "pname",
            "type": "gerrit_review",
            "url": "http://example.com/",
            "topic_id": topic_user_id,
            "state": "active",
        }
        pc = admin.post("/api/v1/components", data=data).data
        component_id = pc["component"]["id"]
        gc = user.get("/api/v1/components/%s" % component_id).data
        assert gc["component"]["name"] == "pname"
        assert gc["component"]["state"] == "active"

        mock_github_result = mock.Mock()
        mock_github_request.get.return_value = mock_github_result

        mock_github_result.status_code = 200
        mock_github_result.json.return_value = {
            "number": 1,  # issue_id
            "title": "Create a GET handler for /componenttype/<ct_name>",
            "user": {"login": "Spredzy"},  # reporter
            "assignee": None,
            "state": "closed",  # status
            "product": "redhat-cip",
            "component": "dci-control-server",
            "created_at": "2015-12-09T09:29:26Z",
            "updated_at": "2015-12-18T15:19:41Z",
            "closed_at": "2015-12-18T15:19:41Z",
        }

        data = {
            "url": "https://github.com/redhat-cip/dci-control-server/issues/1",
            "topic_id": topic_user_id,
        }
        admin.post("/api/v1/components/%s/issues" % component_id, data=data)
        result = user.get("/api/v1/components/%s/issues" % component_id).data
        assert result["issues"][0]["url"] == data["url"]


def test_attach_invalid_issue(admin, job_user_id, topic_user_id):
    data = {"url": '<script>alert("booo")</script>', "topic_id": topic_user_id}
    r = admin.post("/api/v1/jobs/%s/issues" % job_user_id, data=data)
    assert r.status_code == 400


def test_unattach_issue_from_job(user, job_user_id, topic_user_id):
    with mock.patch(GITHUB_TRACKER, spec=requests) as mock_github_request:
        mock_github_result = mock.Mock()
        mock_github_request.get.return_value = mock_github_result

        mock_github_result.status_code = 200
        mock_github_result.json.return_value = {
            "number": 1,  # issue_id
            "title": "Create a GET handler for /componenttype/<ct_name>",
            "user": {"login": "Spredzy"},  # reporter
            "assignee": None,
            "state": "closed",  # status
            "product": "redhat-cip",
            "component": "dci-control-server",
            "created_at": "2015-12-09T09:29:26Z",
            "updated_at": "2015-12-18T15:19:41Z",
            "closed_at": "2015-12-18T15:19:41Z",
        }

        data = {
            "url": "https://github.com/redhat-cip/dci-control-server/issues/1",
            "topic_id": topic_user_id,
        }
        result = user.post("/api/v1/jobs/%s/issues" % job_user_id, data=data)
        issue_id = result.data["issue"]["id"]
        result = user.get("/api/v1/jobs/%s/issues" % job_user_id).data
        assert result["_meta"]["count"] == 1
        user.delete("/api/v1/jobs/%s/issues/%s" % (job_user_id, issue_id))
        result = user.get("/api/v1/jobs/%s/issues" % job_user_id).data
        assert result["_meta"]["count"] == 0


def test_unattach_issue_from_component(admin, user, topic_user_id):
    with mock.patch(GITHUB_TRACKER, spec=requests) as mock_github_request:
        data = {
            "name": "pname",
            "type": "gerrit_review",
            "url": "http://example.com/",
            "topic_id": topic_user_id,
            "state": "active",
        }
        pc = admin.post("/api/v1/components", data=data).data
        component_id = pc["component"]["id"]
        gc = user.get("/api/v1/components/%s" % component_id).data
        assert gc["component"]["name"] == "pname"
        assert gc["component"]["state"] == "active"

        mock_github_result = mock.Mock()
        mock_github_request.get.return_value = mock_github_result

        mock_github_result.status_code = 200
        mock_github_result.json.return_value = {
            "number": 1,  # issue_id
            "title": "Create a GET handler for /componenttype/<ct_name>",
            "user": {"login": "Spredzy"},  # reporter
            "assignee": None,
            "state": "closed",  # status
            "product": "redhat-cip",
            "component": "dci-control-server",
            "created_at": "2015-12-09T09:29:26Z",
            "updated_at": "2015-12-18T15:19:41Z",
            "closed_at": "2015-12-18T15:19:41Z",
        }

        data = {
            "url": "https://github.com/redhat-cip/dci-control-server/issues/1",
            "topic_id": topic_user_id,
        }
        result = admin.post("/api/v1/components/%s/issues" % component_id, data=data)
        issue_id = result.data["issue"]["id"]
        result = user.get("/api/v1/components/%s/issues" % component_id).data
        assert result["_meta"]["count"] == 1
        user.delete("/api/v1/components/%s/issues/%s" % (component_id, issue_id))
        result = user.get("/api/v1/components/%s/issues" % component_id).data
        assert result["_meta"]["count"] == 0


def test_github_tracker(user, job_user_id, topic_user_id):
    with mock.patch(GITHUB_TRACKER, spec=requests) as mock_github_request:
        mock_github_result = mock.Mock()
        mock_github_request.get.return_value = mock_github_result

        mock_github_result.status_code = 200
        mock_github_result.json.return_value = {
            "number": 1,  # issue_id
            "title": "Create a GET handler for /componenttype/<ct_name>",
            "user": {"login": "Spredzy"},  # reporter
            "assignee": None,
            "state": "closed",  # status
            "product": "redhat-cip",
            "component": "dci-control-server",
            "created_at": "2015-12-09T09:29:26Z",
            "updated_at": "2015-12-18T15:19:41Z",
            "closed_at": "2015-12-18T15:19:41Z",
        }

        data = {
            "url": "https://github.com/redhat-cip/dci-control-server/issues/1",
            "topic_id": topic_user_id,
        }
        user.post("/api/v1/jobs/%s/issues" % job_user_id, data=data)
        result = user.get("/api/v1/jobs/%s/issues" % job_user_id).data["issues"][0]

        assert result["status_code"] == 200
        assert result["issue_id"] == 1
        assert result["title"] == ("Create a GET handler for /componenttype/<ct_name>")
        assert result["reporter"] == "Spredzy"
        assert result["status"] == "closed"
        assert result["product"] == "redhat-cip"
        assert result["component"] == "dci-control-server"
        assert result["created_at"] == "2015-12-09T09:29:26Z"
        assert result["updated_at"] == "2015-12-18T15:19:41Z"
        assert result["closed_at"] == "2015-12-18T15:19:41Z"
        assert result["assignee"] is None


def test_github_tracker_with_private_issue(user, job_user_id, topic_user_id):
    with mock.patch(GITHUB_TRACKER, spec=requests) as mock_github_request:
        mock_github_result = mock.Mock()
        mock_github_request.get.return_value = mock_github_result

        mock_github_result.status_code = 404

        data = {
            "url": "https://github.com/redhat-cip/dci-control-server/issues/1",
            "topic_id": topic_user_id,
        }
        user.post("/api/v1/jobs/%s/issues" % job_user_id, data=data)
        result = user.get("/api/v1/jobs/%s/issues" % job_user_id).data["issues"][0]

        assert result["status_code"] == 404
        assert result["issue_id"] == 1
        assert result["title"] == "private issue"
        assert result["reporter"] is None
        assert result["status"] is None
        assert result["product"] == "redhat-cip"
        assert result["component"] == "dci-control-server"
        assert result["created_at"] is None
        assert result["updated_at"] is None
        assert result["closed_at"] is None
        assert result["assignee"] is None


def test_bugzilla_tracker(user, job_user_id, topic_user_id):
    with mock.patch(BUGZILLA_TRACKER, spec=requests) as mock_bugzilla_request:
        mock_bugzilla_result = mock.Mock()
        mock_bugzilla_request.get.return_value = mock_bugzilla_result

        mock_bugzilla_result.status_code = 200
        mock_bugzilla_result.content = """
<bugzilla version="4.4.12051.1"
          urlbase="https://bugzilla.redhat.com/"
          maintainer="bugzilla-requests@redhat.com" >
    <bug>
          <bug_id>1184949</bug_id>
          <creation_ts>2015-01-22 09:46:00 -0500</creation_ts>
          <short_desc>Timeouts in haproxy for keystone can be</short_desc>
          <delta_ts>2016-06-29 18:50:43 -0400</delta_ts>
          <product>Red Hat OpenStack</product>
          <component>rubygem-staypuft</component>
          <bug_status>NEW</bug_status>
          <reporter name="Alfredo Moralejo">amoralej</reporter>
          <assigned_to name="Mike Burns">mburns</assigned_to>
    </bug>
</bugzilla>
"""

        data = {
            "url": "https://bugzilla.redhat.com/show_bug.cgi?id=1184949",
            "topic_id": topic_user_id,
        }
        user.post("/api/v1/jobs/%s/issues" % job_user_id, data=data)
        result = user.get("/api/v1/jobs/%s/issues" % job_user_id).data["issues"][0]

        assert result["status_code"] == 200
        assert result["issue_id"] == "1184949"
        assert result["title"] == "Timeouts in haproxy for keystone can be"
        assert result["reporter"] == "amoralej"
        assert result["assignee"] == "mburns"
        assert result["status"] == "NEW"
        assert result["product"] == "Red Hat OpenStack"
        assert result["component"] == "rubygem-staypuft"
        assert result["created_at"] == "2015-01-22 09:46:00 -0500"
        assert result["updated_at"] == "2016-06-29 18:50:43 -0400"
        assert result["closed_at"] is None


def test_bugzilla_tracker_with_non_existent_issue(user, job_user_id, topic_user_id):
    with mock.patch(BUGZILLA_TRACKER, spec=requests) as mock_bugzilla_request:
        mock_bugzilla_result = mock.Mock()
        mock_bugzilla_request.get.return_value = mock_bugzilla_result

        mock_bugzilla_result.status_code = 400

        data = {
            "url": "https://bugzilla.redhat.com/show_bug.cgi?id=1184949",
            "topic_id": topic_user_id,
        }
        user.post("/api/v1/jobs/%s/issues" % job_user_id, data=data)
        result = user.get("/api/v1/jobs/%s/issues" % job_user_id).data["issues"][0]

        assert result["status_code"] == 400
        assert result["issue_id"] is None
        assert result["title"] is None
        assert result["reporter"] is None
        assert result["assignee"] is None
        assert result["status"] is None
        assert result["product"] is None
        assert result["component"] is None
        assert result["created_at"] is None
        assert result["updated_at"] is None
        assert result["closed_at"] is None


def test_create_get_issues(user, topic_user_id):
    issues = user.get("/api/v1/issues")
    assert issues.data["issues"] == []
    pissue = user.post(
        "/api/v1/issues", data={"url": "http://bugzilla/42", "topic_id": topic_user_id}
    )
    assert pissue.status_code == 201
    pissue_id1 = pissue.data["issue"]["id"]

    pissue = user.post(
        "/api/v1/issues", data={"url": "http://bugzilla/43", "topic_id": topic_user_id}
    )
    assert pissue.status_code == 201
    pissue_id2 = pissue.data["issue"]["id"]
    issues = user.get("/api/v1/issues")
    assert len(issues.data["issues"]) == 2
    assert set([pissue_id1, pissue_id2]) == {i["id"] for i in issues.data["issues"]}

    g_issue_id1 = user.get("/api/v1/issues/%s" % pissue_id1)
    assert g_issue_id1.status_code == 200
    assert g_issue_id1.data["issue"]["url"] == "http://bugzilla/42"

    g_issue_id2 = user.get("/api/v1/issues/%s" % pissue_id2)
    assert g_issue_id2.status_code == 200
    assert g_issue_id2.data["issue"]["url"] == "http://bugzilla/43"


def test_delete_issues(admin, user, topic_user_id):
    pissue = user.post(
        "/api/v1/issues", data={"url": "http://bugzilla/42", "topic_id": topic_user_id}
    )
    assert pissue.status_code == 201
    pissue_id1 = pissue.data["issue"]["id"]
    issues = user.get("/api/v1/issues")
    assert len(issues.data["issues"]) == 1
    pissue_etag = pissue.headers.get("ETag")

    dissue = admin.delete(
        "/api/v1/issues/%s" % pissue_id1, headers={"If-match": pissue_etag}
    )
    assert dissue.status_code == 204
    issues = user.get("/api/v1/issues")
    assert len(issues.data["issues"]) == 0


# test issues - tests
def test_crd_test_to_issue(admin, user, topic_user_id):
    pissue = user.post(
        "/api/v1/issues", data={"url": "http://bugzilla/42", "topic_id": topic_user_id}
    )
    pissue_id1 = pissue.data["issue"]["id"]
    test = user.post("/api/v1/tests", data={"name": "pname1"})
    test_id1 = test.data["test"]["id"]

    # 0 tests from issues pissue_id1
    issues_tests = user.get("/api/v1/issues/%s/tests" % pissue_id1)
    assert len(issues_tests.data["tests"]) == 0

    # associate test_id1 to issue pissue_id1
    ptest = user.post(
        "/api/v1/issues/%s/tests" % pissue_id1, data={"test_id": test_id1}
    )
    assert ptest.status_code == 201

    issues_tests = user.get("/api/v1/issues/%s/tests" % pissue_id1)
    assert len(issues_tests.data["tests"]) == 1
    assert issues_tests.data["tests"][0]["id"] == test_id1

    # remove test_id1 from issue pissue_id1
    admin.delete("/api/v1/issues/%s/tests/%s" % (pissue_id1, test_id1))
    issues_tests = user.get("/api/v1/issues/%s/tests" % pissue_id1)
    assert len(issues_tests.data["tests"]) == 0
