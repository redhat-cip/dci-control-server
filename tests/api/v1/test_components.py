# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2023 Red Hat, Inc
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
from datetime import datetime
import mock
import pytest
import uuid
import time
from dci import dci_config
from dci.api.v1 import components
from dci.stores import files_utils
from dci.common import exceptions as dci_exc


@mock.patch("dci.api.v1.notifications.component_dispatcher")
def test_create_components_active(mock_disp, client_admin, rhel_80_topic_id):
    data = {
        "name": "pname",
        "type": "gerrit_review",
        "url": "http://example.com/",
        "topic_id": rhel_80_topic_id,
        "state": "active",
    }
    pc = client_admin.post("/api/v1/components", data=data).data
    pc_id = pc["component"]["id"]
    gc = client_admin.get("/api/v1/components/%s" % pc_id).data
    assert gc["component"]["name"] == "pname"
    assert gc["component"]["state"] == "active"
    mock_disp.assert_called()


@mock.patch("dci.api.v1.notifications.component_dispatcher")
def test_create_component_with_canonical_project_name(
    mock_disp, client_admin, rhel_80_topic_id
):
    data = {
        "name": "4.12.0 2023-01-12",
        "canonical_project_name": "OpenShift 4.12.0 2023-01-12",
        "type": "ocp",
        "url": "quay.io/openshift-release-dev/ocp-release@sha256:4c5a7e26d707780be6466ddc9591865beb2e3baa5556432d23e8d57966a2dd18",
        "topic_id": rhel_80_topic_id,
    }
    pc = client_admin.post("/api/v1/components", data=data).data
    pc_id = pc["component"]["id"]
    gc = client_admin.get("/api/v1/components/%s" % pc_id).data
    assert gc["component"]["name"] == "4.12.0 2023-01-12"
    assert gc["component"]["canonical_project_name"] == "OpenShift 4.12.0 2023-01-12"
    assert gc["component"]["display_name"] == "OpenShift 4.12.0 2023-01-12"
    assert gc["component"]["version"] == "4.12.0 2023-01-12"
    assert gc["component"]["uid"] == ""
    assert (
        gc["component"]["url"]
        == "quay.io/openshift-release-dev/ocp-release@sha256:4c5a7e26d707780be6466ddc9591865beb2e3baa5556432d23e8d57966a2dd18"
    )
    assert gc["component"]["state"] == "active"
    mock_disp.assert_called()


@mock.patch("dci.api.v1.notifications.component_dispatcher")
def test_create_component_without_canonical_project_name(
    mock_disp, client_admin, rhel_80_topic_id
):
    data = {
        "name": "OpenShift 4.12.0",
        "type": "ocp",
        "url": "quay.io/openshift-release-dev/ocp-release@sha256:4c5a7e26d707780be6466ddc9591865beb2e3baa5556432d23e8d57966a2dd18",
        "topic_id": rhel_80_topic_id,
    }
    pc = client_admin.post("/api/v1/components", data=data).data
    pc_id = pc["component"]["id"]
    gc = client_admin.get("/api/v1/components/%s" % pc_id).data
    assert gc["component"]["name"] == "OpenShift 4.12.0"
    assert gc["component"]["canonical_project_name"] == ""
    assert gc["component"]["display_name"] == "OpenShift 4.12.0"
    assert gc["component"]["version"] == "4.12.0"
    assert (
        gc["component"]["url"]
        == "quay.io/openshift-release-dev/ocp-release@sha256:4c5a7e26d707780be6466ddc9591865beb2e3baa5556432d23e8d57966a2dd18"
    )
    assert gc["component"]["state"] == "active"
    mock_disp.assert_called()


@mock.patch("dci.api.v1.notifications.component_dispatcher")
def test_create_component_with_display_name(mock_disp, client_admin, rhel_80_topic_id):
    data = {
        "display_name": "RHEL-8.6.0-20211205.3",
        "version": "8.6.0-20211205.3",
        "uid": "abc",
        "type": "compose",
        "url": "http://example.org/RHEL-8.6.0-20211205.3",
        "topic_id": rhel_80_topic_id,
    }
    component = client_admin.post("/api/v1/components", data=data).data["component"]
    assert component["name"] == "RHEL-8.6.0-20211205.3"
    assert component["canonical_project_name"] == ""
    assert component["display_name"] == "RHEL-8.6.0-20211205.3"
    assert component["version"] == "8.6.0-20211205.3"
    assert component["uid"] == "abc"
    assert component["url"] == "http://example.org/RHEL-8.6.0-20211205.3"
    assert component["state"] == "active"
    assert component["message"] == ""
    assert component["title"] == ""

    mock_disp.assert_called()


def test_raise_an_error_if_name_and_display_name_are_absent(
    client_admin, rhel_80_topic_id
):
    data = {
        "version": "8.6.0-20211205.3",
        "uid": "abc",
        "type": "compose",
        "url": "http://example.org/RHEL-8.6.0-20211205.3",
        "topic_id": rhel_80_topic_id,
    }
    r = client_admin.post("/api/v1/components", data=data)
    assert r.status_code == 400


def test_raise_an_error_if_name_or_display_name_empty(client_admin, rhel_80_topic_id):
    data = {
        "display_name": "",
        "type": "compose",
        "topic_id": rhel_80_topic_id,
    }
    r = client_admin.post("/api/v1/components", data=data)
    assert r.status_code == 400
    data = {
        "name": "",
        "type": "compose",
        "topic_id": rhel_80_topic_id,
    }
    r = client_admin.post("/api/v1/components", data=data)
    assert r.status_code == 400


@mock.patch("dci.api.v1.notifications.component_dispatcher")
def test_create_component_with_version(mock_disp, client_admin, rhel_80_topic_id):
    data = {
        "name": "RHEL-8.6.0-20211205.3",
        "version": "8.6.0-20211205.3",
        "uid": "abc",
        "type": "compose",
        "url": "http://example.org/RHEL-8.6.0-20211205.3",
        "topic_id": rhel_80_topic_id,
    }
    component = client_admin.post("/api/v1/components", data=data).data["component"]
    assert component["name"] == "RHEL-8.6.0-20211205.3"
    assert component["canonical_project_name"] == ""
    assert component["display_name"] == "RHEL-8.6.0-20211205.3"
    assert component["version"] == "8.6.0-20211205.3"
    assert component["uid"] == "abc"
    assert component["url"] == "http://example.org/RHEL-8.6.0-20211205.3"
    assert component["state"] == "active"
    assert component["message"] == ""
    assert component["title"] == ""

    mock_disp.assert_called()


@mock.patch("dci.api.v1.notifications.component_dispatcher")
def test_create_component_without_version_nor_display_name(
    mock_disp, client_admin, rhel_80_topic_id
):
    data = {
        "name": "dci-openshift-agent 0.5.0-1.202209222145git23657e82.el8",
        "canonical_project_name": "dci-openshift-agent 0.5.0-1.202209222145git23657e82.el8",
        "type": "git",
        "url": "http://example.org/doa0.5.0.1",
        "topic_id": rhel_80_topic_id,
        "state": "active",
    }
    pc = client_admin.post("/api/v1/components", data=data).data
    pc_id = pc["component"]["id"]
    gc = client_admin.get("/api/v1/components/%s" % pc_id).data
    assert (
        gc["component"]["name"]
        == "dci-openshift-agent 0.5.0-1.202209222145git23657e82.el8"
    )
    assert (
        gc["component"]["canonical_project_name"]
        == "dci-openshift-agent 0.5.0-1.202209222145git23657e82.el8"
    )
    assert (
        gc["component"]["display_name"]
        == "dci-openshift-agent 0.5.0-1.202209222145git23657e82.el8"
    )
    assert gc["component"]["version"] == "0.5.0-1.202209222145git23657e82.el8"
    assert gc["component"]["uid"] == ""
    assert gc["component"]["state"] == "active"
    mock_disp.assert_called()


@mock.patch("dci.api.v1.notifications.component_dispatcher")
def test_create_components_inactive(mock_disp, client_admin, rhel_80_topic_id):
    data = {
        "name": "pname",
        "type": "gerrit_review",
        "url": "http://example.com/",
        "topic_id": rhel_80_topic_id,
        "state": "inactive",
    }
    pc = client_admin.post("/api/v1/components", data=data).data
    pc_id = pc["component"]["id"]
    gc = client_admin.get("/api/v1/components/%s" % pc_id).data
    assert gc["component"]["name"] == "pname"
    assert gc["component"]["state"] == "inactive"
    mock_disp.assert_not_called()


def test_create_component_lowercase_type(client_admin, rhel_80_topic_id):
    data = {
        "name": "pname",
        "type": "GERRIT_REVIEW",
        "url": "http://example.com/",
        "topic_id": rhel_80_topic_id,
        "state": "active",
    }
    component = client_admin.post("/api/v1/components", data=data).data["component"]
    component = client_admin.get("/api/v1/components/%s" % component["id"]).data[
        "component"
    ]
    assert component["type"] == "gerrit_review"


def test_create_components_already_exist(client_admin, rhel_80_topic_id):
    data = {"name": "pname", "type": "gerrit_review", "topic_id": rhel_80_topic_id}
    pstatus_code = client_admin.post("/api/v1/components", data=data).status_code
    assert pstatus_code == 201

    pstatus_code = client_admin.post("/api/v1/components", data=data).status_code
    assert pstatus_code == 409


def test_create_components_with_same_name_on_different_topics(
    client_admin, rhel_80_topic_id, rhel_product
):
    data = {"name": "pname", "type": "gerrit_review", "topic_id": rhel_80_topic_id}
    pstatus_code = client_admin.post("/api/v1/components", data=data).status_code
    assert pstatus_code == 201

    topic2 = client_admin.post(
        "/api/v1/topics",
        data={
            "name": "tname",
            "product_id": rhel_product["id"],
            "component_types": ["type1", "type2"],
        },
    ).data
    topic_id2 = topic2["topic"]["id"]

    data = {"name": "pname", "type": "gerrit_review", "topic_id": topic_id2}
    pstatus_code = client_admin.post("/api/v1/components", data=data).status_code
    assert pstatus_code == 201


def test_create_components_with_same_name_on_same_topics(
    client_admin, rhel_80_topic_id
):
    data = {"name": "pname", "type": "gerrit_review", "topic_id": rhel_80_topic_id}
    pc1 = client_admin.post("/api/v1/components", data=data)
    assert pc1.status_code == 201

    pc2 = client_admin.post("/api/v1/components", data=data)
    assert pc2.status_code == 409


def test_name_topic_id_type_team_id_version_uniqueness(
    client_user1, rhel_80_topic_id, team1_id
):
    data = {
        "name": "pname",
        "type": "gerrit_review",
        "topic_id": rhel_80_topic_id,
        "team_id": team1_id,
    }
    p = client_user1.post("/api/v1/components", data=data)
    assert p.status_code == 201

    p = client_user1.post("/api/v1/components", data=data)
    assert p.status_code == 409

    data["version"] = "1.2.3"
    p = client_user1.post("/api/v1/components", data=data)
    assert p.status_code == 201

    p = client_user1.post("/api/v1/components", data=data)
    assert p.status_code == 409


def test_create_components_with_same_name_on_same_topics_different_team(
    client_user1, client_user2, rhel_80_topic_id, team1_id, team2_id
):
    data = {
        "name": "pname",
        "type": "gerrit_review",
        "topic_id": rhel_80_topic_id,
        "team_id": team1_id,
    }
    pstatus_code = client_user1.post("/api/v1/components", data=data).status_code
    assert pstatus_code == 201

    data = {
        "name": "pname",
        "type": "gerrit_review",
        "topic_id": rhel_80_topic_id,
        "team_id": team2_id,
    }
    pstatus_code = client_user2.post("/api/v1/components", data=data).status_code
    assert pstatus_code == 201


def test_recreate_components_with_same_name_on_same_topics(
    client_admin, rhel_80_topic_id
):
    """The goal of this test is to verify that we can:
    - create a component, delete it, then create another component with
      the same name as the previous one
    - create, then delete, then create, then delete, multiple times a
      component with the same name
    """
    for n in range(3):
        data = {"name": "pouet", "type": "gerrit_review", "topic_id": rhel_80_topic_id}
        result = client_admin.post("/api/v1/components", data=data)
        assert result.status_code == 201

        result = client_admin.delete(
            "/api/v1/components/%s" % result.data["component"]["id"],
            headers={"If-match": result.data["component"]["etag"]},
        )
        assert result.status_code == 204


def test_create_components_with_same_name_and_different_type(
    client_admin, rhel_80_topic_id
):
    data = {"name": "pname", "type": "first_type", "topic_id": rhel_80_topic_id}
    pstatus_code = client_admin.post("/api/v1/components", data=data).status_code
    assert pstatus_code == 201

    data = {"name": "pname", "type": "second_type", "topic_id": rhel_80_topic_id}
    pstatus_code = client_admin.post("/api/v1/components", data=data).status_code
    assert pstatus_code == 201


def test_create_component_with_tags(client_admin, rhel_80_topic_id):
    data = {
        "name": "pname",
        "type": "first_type",
        "topic_id": rhel_80_topic_id,
        "tags": ["tag1", "tag2"],
    }
    r = client_admin.post("/api/v1/components", data=data)
    assert r.status_code == 201

    component = r.data["component"]
    r = client_admin.get("/api/v1/components/%s" % component["id"])
    assert r.status_code == 200
    assert r.data["component"]["tags"] == ["tag1", "tag2"]

    r = client_admin.put(
        "/api/v1/components/%s" % component["id"],
        data={"state": "inactive"},
        headers={"If-match": component["etag"]},
    )
    assert r.status_code == 200
    assert r.data["component"]["tags"] == ["tag1", "tag2"]


def test_create_component_with_release_at(client_admin, rhel_80_topic_id):
    released_at = datetime.utcnow().isoformat()
    data = {
        "name": "pname",
        "type": "first_type",
        "topic_id": rhel_80_topic_id,
        "released_at": released_at,
    }
    cmpt = client_admin.post("/api/v1/components", data=data)
    assert cmpt.status_code == 201

    cmpt = client_admin.get("/api/v1/components/%s" % cmpt.data["component"]["id"])
    assert cmpt.status_code == 200

    assert cmpt.data["component"]["released_at"] == released_at


def test_get_all_components_created_after(client_admin, rhel_80_topic_id):
    created_after = int(time.time() * 1000)
    for i in range(5):
        client_admin.post(
            "/api/v1/components",
            data={
                "name": "pname%s" % uuid.uuid4(),
                "type": "gerrit_review",
                "topic_id": rhel_80_topic_id,
            },
        ).data
    db_all_cs = client_admin.get(
        "/api/v1/topics/%s/components?created_after=%s&sort=created_at"
        % (rhel_80_topic_id, created_after)
    ).data
    assert len(db_all_cs["components"]) == 5
    component_2 = db_all_cs["components"][2]

    created_after = int(time.time() * 1000)
    db_all_cs = client_admin.get(
        "/api/v1/topics/%s/components?created_after=%s&sort=created_at"
        % (rhel_80_topic_id, created_after)
    ).data
    assert len(db_all_cs["components"]) == 0

    created_after = component_2["created_at"]
    db_all_cs = client_admin.get(
        "/api/v1/topics/%s/components?created_after=%s&sort=created_at"
        % (rhel_80_topic_id, created_after)
    ).data
    assert len(db_all_cs["components"]) == 3


def test_get_all_components_updated_after(client_admin, rhel_80_topic_id):
    for i in range(5):
        client_admin.post(
            "/api/v1/components",
            data={
                "name": "pname%s" % uuid.uuid4(),
                "type": "gerrit_review",
                "topic_id": rhel_80_topic_id,
            },
        ).data
    db_all_cs = client_admin.get(
        "/api/v1/topics/%s/components?sort=created_at" % rhel_80_topic_id
    ).data
    assert len(db_all_cs["components"]) == 5
    component_2 = db_all_cs["components"][2]

    updated_after = datetime.utcnow().isoformat()
    db_all_cs = client_admin.get(
        "/api/v1/topics/%s/components?updated_after=%s&sort=created_at"
        % (rhel_80_topic_id, updated_after)
    ).data
    assert len(db_all_cs["components"]) == 0

    client_admin.put(
        "/api/v1/components/%s" % component_2["id"],
        headers={"If-match": component_2["etag"]},
        data={"name": "lol"},
    )
    component_2 = client_admin.get("/api/v1/components/%s" % component_2["id"])
    updated_after = component_2.data["component"]["updated_at"]
    db_all_cs = client_admin.get(
        "/api/v1/topics/%s/components?updated_after=%s&sort=created_at"
        % (rhel_80_topic_id, updated_after)
    ).data
    assert len(db_all_cs["components"]) == 1


def test_get_all_components(client_admin, rhel_80_topic_id):
    created_c_ids = []
    for i in range(5):
        pc = client_admin.post(
            "/api/v1/components",
            data={
                "name": "pname%s" % uuid.uuid4(),
                "type": "gerrit_review",
                "topic_id": rhel_80_topic_id,
            },
        ).data
        created_c_ids.append(pc["component"]["id"])
    created_c_ids.sort()

    db_all_cs = client_admin.get("/api/v1/topics/%s/components" % rhel_80_topic_id).data
    db_all_cs = db_all_cs["components"]
    db_all_cs_ids = [db_ct["id"] for db_ct in db_all_cs]
    db_all_cs_ids.sort()

    assert db_all_cs_ids == created_c_ids


def test_get_all_components_not_in_topic(client_admin, client_user1, openstack_product):
    topic = client_admin.post(
        "/api/v1/topics",
        data={
            "name": "topic_test",
            "product_id": openstack_product["id"],
            "component_types": ["type1", "type2"],
        },
    ).data
    topic_id = topic["topic"]["id"]
    res = client_user1.get("/api/v1/topics/%s/components" % topic_id)
    assert res.status_code == 401
    assert res.data["message"] == "Operation not authorized."


def test_get_all_components_with_pagination(client_admin, rhel_80_topic_id):
    # create 20 component types and check meta data count
    for i in range(20):
        client_admin.post(
            "/api/v1/components",
            data={
                "name": "pname%s" % uuid.uuid4(),
                "type": "gerrit_review",
                "topic_id": rhel_80_topic_id,
            },
        )
    cs = client_admin.get("/api/v1/topics/%s/components" % rhel_80_topic_id).data
    assert cs["_meta"]["count"] == 20

    # verify limit and offset are working well
    for i in range(4):
        cs = client_admin.get(
            "/api/v1/topics/%s/components?limit=5&offset=%s"
            % (rhel_80_topic_id, (i * 5))
        ).data
        assert len(cs["components"]) == 5

    # if offset is out of bound, the api returns an empty list
    cs = client_admin.get(
        "/api/v1/topics/%s/components?limit=5&offset=300" % rhel_80_topic_id
    )
    assert cs.status_code == 200
    assert cs.data["components"] == []


def test_get_all_components_with_where_and_query(client_admin, rhel_80_topic_id):
    pc = client_admin.post(
        "/api/v1/components",
        data={"name": "pname1", "type": "gerrit_review", "topic_id": rhel_80_topic_id},
    ).data
    pc_id = pc["component"]["id"]
    client_admin.post(
        "/api/v1/components",
        data={"name": "pname2", "type": "gerrit_review", "topic_id": rhel_80_topic_id},
    ).data

    db_c = client_admin.get(
        "/api/v1/topics/%s/components?where=id:%s" % (rhel_80_topic_id, pc_id)
    ).data
    db_c_id = db_c["components"][0]["id"]
    assert db_c_id == pc_id

    db_c = client_admin.get(
        "/api/v1/topics/%s/components?where=name:pname1" % rhel_80_topic_id
    ).data
    db_c_id = db_c["components"][0]["id"]
    assert db_c_id == pc_id
    assert db_c["_meta"]["count"] == 1

    db_c = client_admin.get(
        "/api/v1/topics/%s/components?query=eq(name,pname1)" % rhel_80_topic_id
    ).data
    assert db_c["_meta"]["count"] == 1
    db_c_id = db_c["components"][0]["id"]
    assert db_c_id == pc_id

    db_c = client_admin.get(
        "/api/v1/topics/%s/components?query=and(eq(name,pname1),null(url))"
        % rhel_80_topic_id
    ).data
    assert db_c["_meta"]["count"] == 1
    db_c_id = db_c["components"][0]["id"]
    assert db_c_id == pc_id

    db_c = client_admin.get(
        "/api/v1/topics/%s/components?query=and(eq(name,pname1),not(null(url)))"
        % rhel_80_topic_id
    ).data
    assert db_c["_meta"]["count"] == 0

    db_c = client_admin.get(
        "/api/v1/topics/%s/components?query=and(eq(name,pname1),eq(type,gerrit_review),eq(topic_id,%s))"
        % (rhel_80_topic_id, rhel_80_topic_id)
    ).data
    db_c_id = db_c["components"][0]["id"]
    assert db_c_id == pc_id
    assert db_c["_meta"]["count"] == 1


def test_nrt_get_all_components_with_new_line_in_where(client_admin, rhel_80_topic_id):
    response = client_admin.get(
        "/api/v1/topics/%s/components?sort=-created_at&where=name:RHOS-16.2-RHEL-8-20221005.n.1-\nASYNC,type:compose,state:active&limit=1&offset=0"
        % rhel_80_topic_id
    )
    assert response.status_code == 200


def test_where_invalid(client_admin, rhel_80_topic_id):
    err = client_admin.get("/api/v1/topics/%s/components?where=id" % rhel_80_topic_id)

    assert err.status_code == 400
    assert err.data["message"] == "Request malformed"
    assert err.data["payload"]["error"] == "where: 'id' is not a 'key value csv'"


def test_get_component_by_id_or_name(client_admin, rhel_80_topic_id):
    data = {
        "name": "pname",
        "type": "gerrit_review",
        "topic_id": rhel_80_topic_id,
    }
    pc = client_admin.post("/api/v1/components", data=data).data
    pc_id = pc["component"]["id"]

    # get by uuid
    created_ct = client_admin.get("/api/v1/components/%s" % pc_id)
    assert created_ct.status_code == 200

    created_ct = created_ct.data
    assert created_ct["component"]["id"] == pc_id


def test_nrt_get_component_by_id_return_list_of_jobs_only_from_team_of_the_user(
    team_admin_job, client_admin, client_user1
):
    component = client_admin.get("/api/v1/jobs/%s" % team_admin_job["id"]).data["job"][
        "components"
    ][0]

    assert len(client_user1.get("/api/v1/jobs").data["jobs"]) == 0
    assert (
        len(
            client_user1.get("/api/v1/components/%s" % component["id"]).data[
                "component"
            ]["jobs"]
        )
        == 0
    )


def test_nrt_get_component_by_id_return_list_of_jobs_if_rh_employee(
    team_admin_job, client_admin, client_rh_employee
):
    component = client_admin.get("/api/v1/jobs/%s" % team_admin_job["id"]).data["job"][
        "components"
    ][0]

    assert len(client_rh_employee.get("/api/v1/jobs").data["jobs"]) == 1
    jobs = client_rh_employee.get("/api/v1/components/%s" % component["id"]).data[
        "component"
    ]["jobs"]
    assert len(jobs) == 1
    assert jobs[0]["id"] == team_admin_job["id"]


def test_get_component_not_found(client_admin):
    result = client_admin.get("/api/v1/components/ptdr")
    assert result.status_code == 404


def test_delete_component_by_id(client_admin, hmac_client_feeder, rhel_80_topic_id):
    data = {"name": "pname", "type": "gerrit_review", "topic_id": rhel_80_topic_id}
    pc = hmac_client_feeder.post("/api/v1/components", data=data)
    pc_id = pc.data["component"]["id"]
    assert pc.status_code == 201

    created_ct = client_admin.get("/api/v1/components/%s" % pc_id)
    assert created_ct.status_code == 200

    deleted_ct = client_admin.delete(
        "/api/v1/components/%s" % pc_id,
        headers={"If-match": pc.data["component"]["etag"]},
    )
    assert deleted_ct.status_code == 204

    gct = client_admin.get("/api/v1/components/%s" % pc_id)
    assert gct.status_code == 404


def test_get_all_components_with_sort(client_admin, rhel_80_topic_id):
    # create 4 components ordered by created time
    data = {
        "name": "pname1",
        "title": "aaa",
        "type": "gerrit_review",
        "topic_id": rhel_80_topic_id,
    }
    ct_1_1 = client_admin.post("/api/v1/components", data=data).data["component"]
    data = {
        "name": "pname2",
        "title": "aaa",
        "type": "gerrit_review",
        "topic_id": rhel_80_topic_id,
    }
    ct_1_2 = client_admin.post("/api/v1/components", data=data).data["component"]
    data = {
        "name": "pname3",
        "title": "bbb",
        "type": "gerrit_review",
        "topic_id": rhel_80_topic_id,
    }
    ct_2_1 = client_admin.post("/api/v1/components", data=data).data["component"]
    data = {
        "name": "pname4",
        "title": "bbb",
        "type": "gerrit_review",
        "topic_id": rhel_80_topic_id,
    }
    ct_2_2 = client_admin.post("/api/v1/components", data=data).data["component"]

    cts = client_admin.get(
        "/api/v1/topics/%s/components?sort=created_at" % rhel_80_topic_id
    ).data
    cts_id = [db_cts["id"] for db_cts in cts["components"]]
    assert cts_id == [ct_1_1["id"], ct_1_2["id"], ct_2_1["id"], ct_2_2["id"]]

    # sort by title first and then reverse by created_at
    cts = client_admin.get(
        "/api/v1/topics/%s/components?sort=title,-created_at" % rhel_80_topic_id
    ).data
    cts_id = [db_cts["id"] for db_cts in cts["components"]]
    assert cts_id == [ct_1_2["id"], ct_1_1["id"], ct_2_2["id"], ct_2_1["id"]]


def test_delete_component_not_found(client_admin):
    result = client_admin.delete(
        "/api/v1/components/%s" % uuid.uuid4(), headers={"If-match": "mdr"}
    )
    assert result.status_code == 404


def test_update_component(client_admin, rhel_80_topic_id):
    data = {
        "name": "pname1",
        "title": "aaa",
        "type": "gerrit_review",
        "topic_id": rhel_80_topic_id,
    }

    ct_1 = client_admin.post("/api/v1/components", data=data).data["component"]

    # Active component
    url = "/api/v1/components/%s" % ct_1["id"]
    data = {"name": "cname2"}
    headers = {"If-match": ct_1["etag"]}
    client_admin.put(url, data=data, headers=headers)

    ct_2 = client_admin.get("/api/v1/components/%s" % ct_1["id"]).data["component"]

    assert ct_1["etag"] != ct_2["etag"]
    assert ct_2["name"] == "cname2"


def test_update_component_v2(client_admin, rhel_80_topic_id):
    released_at = datetime.utcnow().isoformat()
    data = {
        "name": "RHEL-8.6.0-20211205.3",
        "version": "8.6.0-20211205.3",
        "type": "compose",
        "url": "http://example.org/RHEL-8.6.0-20211205.3",
        "topic_id": rhel_80_topic_id,
        "released_at": released_at,
        "state": "inactive",
    }
    component = client_admin.post("/api/v1/components", data=data).data["component"]
    assert component["name"] == "RHEL-8.6.0-20211205.3"
    assert component["version"] == "8.6.0-20211205.3"
    assert component["released_at"] == released_at
    assert component["state"] == "inactive"

    new_released_at = datetime.utcnow().isoformat()
    component["name"] = "RHEL-8.6.0-20211205.4"
    component["version"] = "8.6.0-20211205.4"
    component["url"] = "http://example.org/RHEL-8.6.0-20211205.4"
    component["released_at"] = new_released_at
    component["state"] = "active"

    updated_component = client_admin.put(
        "/api/v1/components/%s" % component["id"],
        data=component,
        headers={"If-match": component["etag"]},
    ).data["component"]

    assert updated_component["name"] == "RHEL-8.6.0-20211205.4"
    assert updated_component["version"] == "8.6.0-20211205.4"
    assert updated_component["released_at"] == new_released_at
    assert updated_component["state"] == "active"


@mock.patch("dci.api.v1.notifications.component_dispatcher")
def test_put_component_from_inactive_to_active(
    mock_disp, client_admin, client_user1, rhel_80_topic_id
):
    data = {
        "name": "pname1",
        "title": "aaa",
        "type": "gerrit_review",
        "topic_id": rhel_80_topic_id,
        "state": "inactive",
    }

    ct_1 = client_admin.post("/api/v1/components", data=data).data["component"]
    mock_disp.assert_not_called()

    url = "/api/v1/components/%s" % ct_1["id"]
    data = {"name": "cname2", "state": "active"}
    headers = {"If-match": ct_1["etag"]}
    client_admin.put(url, data=data, headers=headers)
    mock_disp.assert_called()


def test_update_component_with_tags(client_admin, rhel_80_topic_id):
    data = {
        "name": "pname",
        "type": "first_type",
        "topic_id": rhel_80_topic_id,
        "tags": ["tag1", "tag2"],
    }
    cmpt = client_admin.post("/api/v1/components", data=data)
    assert cmpt.status_code == 201

    etag = cmpt.data["component"]["etag"]
    data = {"tags": ["hihi", "haha"]}
    client_admin.put(
        "/api/v1/components/%s" % cmpt.data["component"]["id"],
        data=data,
        headers={"If-match": etag},
    )

    cmpt = client_admin.get("/api/v1/components/%s" % cmpt.data["component"]["id"])
    assert cmpt.data["component"]["tags"] == ["hihi", "haha"]


def test_update_component_lowercase_type(client_admin, rhel_80_topic_id):
    data = {
        "name": "pname",
        "type": "GERRIT_REVIEW",
        "url": "http://example.com/",
        "topic_id": rhel_80_topic_id,
        "state": "active",
    }
    component = client_admin.post("/api/v1/components", data=data).data["component"]
    component = client_admin.put(
        "/api/v1/components/%s" % component["id"],
        data={"type": "METADATA"},
        headers={"If-match": component["etag"]},
    ).data["component"]
    assert component["type"] == "metadata"


def test_add_file_to_component(client_admin, rhel_80_topic_id):
    def create_ct(name):
        data = {
            "name": name,
            "title": "aaa",
            "type": "gerrit_review",
            "topic_id": rhel_80_topic_id,
        }
        return client_admin.post("/api/v1/components", data=data).data["component"]

    ct_1 = create_ct("pname1")
    ct_2 = create_ct("pname2")

    cts = client_admin.get("/api/v1/components/%s?embed=files" % ct_1["id"]).data
    assert len(cts["component"]["files"]) == 0

    url = "/api/v1/components/%s/files" % ct_1["id"]
    c_file = client_admin.post(url, data="lol")
    c_file_1_id = c_file.data["component_file"]["id"]
    url = "/api/v1/components/%s/files" % ct_2["id"]
    c_file = client_admin.post(url, data="lol2")
    c_file_2_id = c_file.data["component_file"]["id"]

    assert c_file.status_code == 201
    l_file = client_admin.get(url)
    assert l_file.status_code == 200
    assert l_file.data["_meta"]["count"] == 1
    assert l_file.data["component_files"][0]["component_id"] == ct_2["id"]
    cts = client_admin.get("/api/v1/components/%s?embed=files" % ct_1["id"]).data
    assert len(cts["component"]["files"]) == 1
    assert cts["component"]["files"][0]["size"] == 5

    cts = client_admin.get("/api/v1/components/%s/files" % ct_1["id"]).data
    assert cts["component_files"][0]["id"] == c_file_1_id

    cts = client_admin.get("/api/v1/components/%s/files" % ct_2["id"]).data
    assert cts["component_files"][0]["id"] == c_file_2_id


def test_download_file_from_component(client_admin, rhel_80_topic_id):
    data = {
        "name": "pname1",
        "title": "aaa",
        "type": "gerrit_review",
        "topic_id": rhel_80_topic_id,
    }
    ct_1 = client_admin.post("/api/v1/components", data=data).data["component"]

    url = "/api/v1/components/%s/files" % ct_1["id"]
    data = "lollollel"
    c_file = client_admin.post(url, data=data).data["component_file"]

    url = "/api/v1/components/%s/files/%s/content" % (ct_1["id"], c_file["id"])
    d_file = client_admin.get(url)
    assert d_file.status_code == 200
    assert d_file.data == '"lollollel"'


def test_delete_file_from_component(client_admin, rhel_80_topic_id):
    data = {
        "name": "pname1",
        "title": "aaa",
        "type": "gerrit_review",
        "topic_id": rhel_80_topic_id,
    }
    ct_1 = client_admin.post("/api/v1/components", data=data).data["component"]

    url = "/api/v1/components/%s/files" % ct_1["id"]
    data = "lol"
    c_file = client_admin.post(url, data=data).data["component_file"]
    url = "/api/v1/components/%s/files" % ct_1["id"]
    g_files = client_admin.get(url)
    assert g_files.data["_meta"]["count"] == 1

    url = "/api/v1/components/%s/files/%s" % (ct_1["id"], c_file["id"])
    d_file = client_admin.delete(url, headers={"If-match": c_file["etag"]})
    assert d_file.status_code == 204

    url = "/api/v1/components/%s/files" % ct_1["id"]
    g_files = client_admin.get(url)
    assert g_files.data["_meta"]["count"] == 0


def test_change_component_state(client_admin, rhel_80_topic_id):
    data = {
        "name": "pname",
        "type": "gerrit_review",
        "url": "http://example.com/",
        "topic_id": rhel_80_topic_id,
        "state": "active",
    }
    pc = client_admin.post("/api/v1/components", data=data).data
    pc_id = pc["component"]["id"]

    t = client_admin.get("/api/v1/components/" + pc_id).data["component"]
    data = {"state": "inactive"}
    r = client_admin.put(
        "/api/v1/components/" + pc_id, data=data, headers={"If-match": t["etag"]}
    )
    assert r.status_code == 200
    assert r.data["component"]["state"] == "inactive"


def test_change_component_to_invalid_state(client_admin, rhel_80_topic_id):
    data = {
        "name": "pname",
        "type": "gerrit_review",
        "url": "http://example.com/",
        "topic_id": rhel_80_topic_id,
        "state": "active",
    }
    pc = client_admin.post("/api/v1/components", data=data).data
    pc_id = pc["component"]["id"]

    t = client_admin.get("/api/v1/components/" + pc_id).data["component"]
    data = {"state": "kikoolol"}
    r = client_admin.put(
        "/api/v1/components/" + pc_id, data=data, headers={"If-match": t["etag"]}
    )
    assert r.status_code == 400
    current_component = client_admin.get("/api/v1/components/" + pc_id)
    assert current_component.status_code == 200
    assert current_component.data["component"]["state"] == "active"


def test_component_success_update_field_by_field(client_admin, rhel_80_topic_id):
    data = {"name": "pname", "type": "gerrit_review", "topic_id": rhel_80_topic_id}
    c = client_admin.post("/api/v1/components", data=data).data["component"]

    client_admin.put(
        "/api/v1/components/%s" % c["id"],
        data={"state": "inactive"},
        headers={"If-match": c["etag"]},
    )

    c = client_admin.get("/api/v1/components/%s" % c["id"]).data["component"]

    assert c["name"] == "pname"
    assert c["state"] == "inactive"
    assert c["title"] == ""

    c = client_admin.put(
        "/api/v1/components/%s" % c["id"],
        data={"name": "pname2"},
        headers={"If-match": c["etag"]},
    ).data["component"]

    assert c["name"] == "pname2"
    assert c["state"] == "inactive"
    assert c["title"] == ""

    client_admin.put(
        "/api/v1/components/%s" % c["id"],
        data={"title": "a new title"},
        headers={"If-match": c["etag"]},
    )

    c = client_admin.get("/api/v1/components/%s" % c["id"]).data["component"]

    assert c["name"] == "pname2"
    assert c["state"] == "inactive"
    assert c["title"] == "a new title"


def create_component(admin, topic_id, ct, name):
    data = {"topic_id": topic_id, "name": name, "type": ct}
    component = admin.post("/api/v1/components", data=data).data
    return str(component["component"]["id"])


def test_get_last_components_by_type(session, client_admin, rhel_80_topic):
    components_ids = []
    for i in range(3):
        cid = create_component(
            client_admin, rhel_80_topic["id"], "puddle_osp", "name-%s" % i
        )
        components_ids.append(cid)

    last_components = components.get_last_components_by_type(
        ["puddle_osp"], topic_id=rhel_80_topic["id"], session=session
    )
    assert str(last_components[0].id) == components_ids[-1]


def test_verify_and_get_components_ids(
    session, client_admin, rhel_80_topic, rhel_80_topic_id
):
    # components types not valid
    with pytest.raises(dci_exc.DCIException):
        components.verify_and_get_components_ids(
            rhel_80_topic["id"], [], ["puddle_osp"], session=session
        )

    with pytest.raises(dci_exc.DCIException):
        components.verify_and_get_components_ids(
            rhel_80_topic["id"],
            [str(uuid.uuid4())],
            ["puddle_osp"],
            session=session,
        )

    # duplicated component types
    c1 = create_component(client_admin, rhel_80_topic_id, "type1", "n1")
    c2 = create_component(client_admin, rhel_80_topic_id, "type1", "n2")
    c3 = create_component(client_admin, rhel_80_topic_id, "type2", "n3")
    with pytest.raises(dci_exc.DCIException):
        components.verify_and_get_components_ids(
            rhel_80_topic_id,
            [c1, c2, c3],
            ["type_1", "type_2", "type_3"],
            session=session,
        )

    cids = components.verify_and_get_components_ids(
        rhel_80_topic_id,
        [c1, c3],
        ["type_1", "type_2"],
        session=session,
    )
    assert set(cids) == {c1, c3}


def test_purge(client_admin, rhel_80_topic_id, rhel_80_component):
    component_id = rhel_80_component["id"]
    store = dci_config.get_store()

    url = "/api/v1/components/%s/files" % component_id
    c_file1 = client_admin.post(url, data="lol")
    assert c_file1.status_code == 201

    path1 = files_utils.build_file_path(
        rhel_80_topic_id, component_id, c_file1.data["component_file"]["id"]
    )
    store.get("components", path1)

    url = "/api/v1/components/%s/files" % component_id
    c_file2 = client_admin.post(url, data="lol")
    assert c_file2.status_code == 201

    path2 = files_utils.build_file_path(
        rhel_80_topic_id, component_id, c_file2.data["component_file"]["id"]
    )
    store.get("components", path2)

    component = client_admin.get("/api/v1/components/%s" % component_id).data[
        "component"
    ]
    client_admin.delete(
        "/api/v1/components/%s" % component_id, headers={"If-match": component["etag"]}
    )
    to_purge = client_admin.get("/api/v1/components/purge").data
    assert len(to_purge["components"]) == 1
    c_purged = client_admin.post("/api/v1/components/purge")
    assert c_purged.status_code == 204

    with pytest.raises(dci_exc.StoreException):
        store.get("components", path1)

    with pytest.raises(dci_exc.StoreException):
        store.get("components", path2)

    to_purge = client_admin.get("/api/v1/components/purge").data
    assert len(to_purge["components"]) == 0


def test_purge_failure(client_admin, rhel_80_topic_id, rhel_80_component):
    component_id = rhel_80_component["id"]

    url = "/api/v1/components/%s/files" % component_id
    c_file1 = client_admin.post(url, data="lol")
    assert c_file1.status_code == 201

    c_files = client_admin.get("/api/v1/components/%s/files" % component_id)
    assert len(c_files.data["component_files"]) == 1

    component = client_admin.get("/api/v1/components/%s" % component_id).data[
        "component"
    ]
    d_component = client_admin.delete(
        "/api/v1/components/%s" % component_id, headers={"If-match": component["etag"]}
    )
    assert d_component.status_code == 204
    to_purge = client_admin.get("/api/v1/components/purge").data
    assert len(to_purge["components"]) == 1
    # purge will fail
    with mock.patch("dci.stores.s3.S3.delete") as mock_delete:
        path1 = files_utils.build_file_path(
            rhel_80_topic_id, component_id, c_file1.data["component_file"]["id"]
        )
        mock_delete.side_effect = dci_exc.StoreException("error")
        purge_res = client_admin.post("/api/v1/components/purge")
        assert purge_res.status_code == 400
        store = dci_config.get_store()
        store.get("components", path1)
        to_purge = client_admin.get("/api/v1/components/purge").data
        assert len(to_purge["components"]) == 1


def test_create_component_as_feeder(client_admin, rhel_80_topic_id, hmac_client_feeder):
    data = {
        "name": "c1",
        "type": "snapshot",
        "topic_id": rhel_80_topic_id,
        "state": "active",
    }
    c = hmac_client_feeder.post("/api/v1/components", data=data).data["component"]
    component = client_admin.get("/api/v1/components/%s" % c["id"]).data["component"]
    assert component["name"] == "c1"
    assert component["state"] == "active"


def test_update_component_as_feeder(client_admin, rhel_80_topic_id, hmac_client_feeder):
    data = {
        "name": "c1",
        "type": "snapshot",
        "topic_id": rhel_80_topic_id,
        "state": "active",
    }
    c = hmac_client_feeder.post("/api/v1/components", data=data).data["component"]
    hmac_client_feeder.put(
        "/api/v1/components/%s" % c["id"],
        data={"type": "tar"},
        headers={"If-match": c["etag"]},
    )
    component = client_admin.get("/api/v1/components/%s" % c["id"]).data["component"]
    assert component["name"] == "c1"
    assert component["type"] == "tar"


def test_create_component_not_allowed_for_user_and_remoteci(
    client_user1, hmac_client_team1, rhel_80_topic_id
):
    data = {
        "name": "c1",
        "type": "snapshot",
        "topic_id": rhel_80_topic_id,
        "state": "active",
    }
    c = client_user1.post("/api/v1/components", data=data)
    assert c.status_code == 401
    c = hmac_client_team1.post("/api/v1/components", data=data)
    assert c.status_code == 401


# ######### tests teams components


def test_create_teams_components(client_user1, team1_id, rhel_80_topic_id):
    data = {
        "name": "pname",
        "type": "gerrit_review",
        "url": "http://example.com/",
        "team_id": team1_id,
        "topic_id": rhel_80_topic_id,
        "state": "active",
    }
    pc = client_user1.post("/api/v1/components", data=data).data
    pc_id = pc["component"]["id"]

    gc = client_user1.get("/api/v1/components/%s" % pc_id).data
    assert gc["component"]["name"] == "pname"
    assert gc["component"]["state"] == "active"


def test_get_all_teams_components(client_user1, team1_id, rhel_80_topic_id):
    data = {
        "name": "pname",
        "type": "gerrit_review",
        "url": "http://example.com/",
        "team_id": team1_id,
        "topic_id": rhel_80_topic_id,
        "state": "active",
    }
    pc = client_user1.post("/api/v1/components", data=data).data
    pc_id = pc["component"]["id"]
    cmpts = client_user1.get(
        "/api/v1/topics/%s/components?where=team_id:%s" % (rhel_80_topic_id, team1_id)
    ).data
    assert cmpts["components"][0]["id"] == pc_id


def test_update_teams_components(client_user1, team1_id, rhel_80_topic_id):
    data = {
        "name": "pname",
        "type": "gerrit_review",
        "url": "http://example.com/",
        "team_id": team1_id,
        "topic_id": rhel_80_topic_id,
        "state": "active",
    }
    pc = client_user1.post("/api/v1/components", data=data).data
    pc_id = pc["component"]["id"]
    etag = pc["component"]["etag"]
    client_user1.put(
        "/api/v1/components/%s" % pc_id,
        data={"name": "pname2"},
        headers={"If-match": etag},
    )
    gc = client_user1.get("/api/v1/components/%s" % pc_id).data
    assert gc["component"]["name"] == "pname2"


def test_delete_teams_components(client_user1, team1_id, rhel_80_topic_id):
    data = {
        "name": "pname",
        "type": "gerrit_review",
        "url": "http://example.com/",
        "team_id": team1_id,
        "topic_id": rhel_80_topic_id,
        "state": "active",
    }
    pc = client_user1.post("/api/v1/components", data=data).data
    pc_id = pc["component"]["id"]

    gc = client_user1.get("/api/v1/components/%s" % pc_id)
    assert gc.status_code == 200

    gc = client_user1.delete(
        "/api/v1/components/%s" % pc_id, headers={"If-match": pc["component"]["etag"]}
    )
    assert gc.status_code == 204

    gc = client_user1.get("/api/v1/components/%s" % pc_id)
    assert gc.status_code == 404


def test_filter_teams_components_by_tag(client_user1, team1_id, rhel_80_topic_id):
    data = {
        "name": "pname",
        "type": "mytest",
        "team_id": team1_id,
        "topic_id": rhel_80_topic_id,
        "tags": ["tag1", "common"],
    }
    client_user1.post("/api/v1/components", data=data).data

    data = {
        "name": "pname",
        "type": "mylib",
        "team_id": team1_id,
        "topic_id": rhel_80_topic_id,
        "tags": ["tag2", "common"],
    }
    client_user1.post("/api/v1/components", data=data).data

    res = client_user1.get(
        "/api/v1/topics/%s/components?where=tags:tag1,team_id:%s"
        % (rhel_80_topic_id, team1_id)
    )
    assert len(res.data["components"]) == 1
    assert "tag1" in res.data["components"][0]["tags"]
    assert "tag2" not in res.data["components"][0]["tags"]

    res = client_user1.get(
        "/api/v1/topics/%s/components?query=and(contains(tags,tag1),eq(team_id,%s))"
        % (rhel_80_topic_id, team1_id)
    )
    assert len(res.data["components"]) == 1
    assert "tag1" in res.data["components"][0]["tags"]
    assert "tag2" not in res.data["components"][0]["tags"]

    res = client_user1.get(
        "/api/v1/topics/%s/components?where=tags:common,team_id:%s"
        % (rhel_80_topic_id, team1_id)
    )
    assert len(res.data["components"]) == 2
    assert "common" in res.data["components"][0]["tags"]
    assert "common" in res.data["components"][1]["tags"]


def test_teams_components_isolation(
    client_user1, client_user2, rhel_80_topic_id, team1_id, team2_id
):
    data = {
        "name": "pname",
        "type": "mytest",
        "topic_id": rhel_80_topic_id,
        "team_id": team1_id,
    }
    pc = client_user1.post("/api/v1/components", data=data)
    assert pc.status_code == 201

    components = client_user1.get(
        "/api/v1/topics/%s/components?where=team_id:%s" % (rhel_80_topic_id, team1_id)
    ).data
    assert components["components"][0]["team_id"] == team1_id

    data = {
        "name": "pname",
        "type": "mytest",
        "topic_id": rhel_80_topic_id,
        "team_id": team2_id,
    }
    pc = client_user1.post("/api/v1/components", data=data)
    assert pc.status_code == 401
    pc = client_user2.post("/api/v1/components", data=data)
    assert pc.status_code == 201

    components = client_user2.get(
        "/api/v1/topics/%s/components?where=team_id:%s" % (rhel_80_topic_id, team1_id)
    )
    assert components.status_code == 200
    assert components.data["components"] == []
    components = client_user2.get(
        "/api/v1/topics/%s/components?where=team_id:%s" % (rhel_80_topic_id, team2_id)
    )
    assert components.status_code == 200
    assert components.data["components"][0]["team_id"] == team2_id


def test_components_access_of_other_teams(
    client_admin,
    client_user1,
    client_user2,
    rhel_80_topic_id,
    team1_id,
    team2_id,
    team3_id,
):
    # create a component associated to team_user_id
    data = {
        "name": "pname",
        "type": "mytest",
        "topic_id": rhel_80_topic_id,
        "team_id": team1_id,
    }
    pc = client_user1.post("/api/v1/components", data=data)
    assert pc.status_code == 201

    components = client_user1.get(
        "/api/v1/topics/%s/components?where=team_id:%s" % (rhel_80_topic_id, team1_id)
    ).data
    assert components["components"][0]["team_id"] == team1_id

    # create a component associated to team_user_id2
    data = {
        "name": "pname",
        "type": "mytest",
        "topic_id": rhel_80_topic_id,
        "team_id": team2_id,
    }
    pc = client_user2.post("/api/v1/components", data=data)
    assert pc.status_code == 201

    # user doesn't have access to team_user_id2's components
    components = client_user1.get(
        "/api/v1/topics/%s/components?where=team_id:%s" % (rhel_80_topic_id, team2_id)
    )
    assert components.status_code == 200
    assert components.data["components"] == []

    permissions = client_admin.get("/api/v1/teams/%s/permissions/components" % team1_id)
    assert permissions.data["teams"] == []

    # team_user_id has now access to the components of team_user_id2
    cat = client_admin.post(
        "/api/v1/teams/%s/permissions/components" % team1_id,
        data={"teams_ids": [team2_id]},
    )
    assert cat.status_code == 201

    # don't raise errors if the permission is already set
    # team_user_id has now access to the components of team_user_id2 and team_user_id3
    cat = client_admin.post(
        "/api/v1/teams/%s/permissions/components" % team1_id,
        data={"teams_ids": [team2_id, team3_id]},
    )
    assert cat.status_code == 201

    permissions = client_admin.get("/api/v1/teams/%s/permissions/components" % team1_id)
    assert permissions.data["teams"][0]["id"] in {team2_id, team3_id}
    assert permissions.data["teams"][1]["id"] in {team2_id, team3_id}

    components = client_user1.get(
        "/api/v1/topics/%s/components?where=team_id:%s" % (rhel_80_topic_id, team2_id)
    )
    assert components.status_code == 200
    assert components.data["components"][0]["team_id"] == team2_id

    # team_user_id has no longer access to the components of team_user_id2 and team_user_id3
    cat = client_admin.delete(
        "/api/v1/teams/%s/permissions/components" % team1_id,
        data={"teams_ids": [team2_id, team3_id]},
    )
    assert cat.status_code == 204

    permissions = client_admin.get("/api/v1/teams/%s/permissions/components" % team1_id)
    assert permissions.data["teams"] == []

    components = client_user1.get(
        "/api/v1/topics/%s/components?where=team_id:%s" % (rhel_80_topic_id, team2_id)
    )
    assert components.status_code == 200
    assert components.data["components"] == []

    # test unable to add permission to the same team
    cat = client_admin.post(
        "/api/v1/teams/%s/permissions/components" % team1_id,
        data={"teams_ids": [team1_id, team2_id]},
    )
    assert cat.status_code == 201

    permissions = client_admin.get("/api/v1/teams/%s/permissions/components" % team1_id)
    assert permissions.status_code == 200
    assert len(permissions.data["teams"]) == 1
    assert permissions.data["teams"][0]["id"] == team2_id


def test_components_access_by_id(
    client_admin, client_user1, client_user2, rhel_80_topic_id, team1_id, team2_id
):
    data = {
        "name": "pname",
        "type": "mytest",
        "topic_id": rhel_80_topic_id,
        "team_id": team1_id,
    }
    pc = client_user1.post("/api/v1/components", data=data)
    assert pc.status_code == 201

    data = {
        "name": "pname",
        "type": "mytest",
        "topic_id": rhel_80_topic_id,
        "team_id": team2_id,
    }
    pc = client_user2.post("/api/v1/components", data=data)
    assert pc.status_code == 201
    pc_team_user_id2 = pc.data["component"]["id"]

    c = client_user2.get("/api/v1/components/%s" % pc_team_user_id2)
    assert c.status_code == 200

    c = client_user1.get("/api/v1/components/%s" % pc_team_user_id2)
    assert c.status_code == 401

    # team_user_id has now access to the components of team_user_id2
    cat = client_admin.post(
        "/api/v1/teams/%s/permissions/components" % team1_id,
        data={"teams_ids": [team2_id]},
    )
    assert cat.status_code == 201

    c = client_user1.get("/api/v1/components/%s" % pc_team_user_id2)
    assert c.status_code == 200


# S3 components related tests


def test_get_component_file_from_s3_user_team_in_RHEL_with_released_component(
    client_admin,
    hmac_client_team1,
    team1_remoteci,
    rhel_product,
    rhel_80_component,
):
    r = hmac_client_team1.get(
        "/api/v1/components/%s/files/.composeinfo" % rhel_80_component["id"]
    )
    assert r.status_code == 302

    s3_endpoint_url = dci_config.CONFIG["STORE_S3_ENDPOINT_URL"]
    bucket = dci_config.CONFIG["STORE_COMPONENTS_CONTAINER"]
    assert r.headers["Location"].startswith(
        f"{s3_endpoint_url}/{bucket}/{rhel_80_component['id']}/.composeinfo"
    )

    r = hmac_client_team1.head(
        "/api/v1/components/%s/files/.composeinfo" % rhel_80_component["id"]
    )
    assert r.status_code == 302
    assert r.headers["Location"].startswith(
        f"{s3_endpoint_url}/{bucket}/{rhel_80_component['id']}/.composeinfo"
    )

    # delete product team permission
    r = client_admin.delete(
        "/api/v1/products/%s/teams/%s"
        % (rhel_product["id"], team1_remoteci["team_id"]),
    )
    assert r.status_code == 204

    r = hmac_client_team1.get(
        "/api/v1/components/%s/files/.composeinfo" % rhel_80_component["id"]
    )
    assert r.status_code == 401

    r = hmac_client_team1.head(
        "/api/v1/components/%s/files/.composeinfo" % rhel_80_component["id"]
    )
    assert r.status_code == 401


def test_get_component_file_from_s3_user_team_in_RHEL_with_pre_release_component(
    client_admin,
    hmac_client_team1,
    team1,
    rhel_81_component,
):
    r = hmac_client_team1.get(
        "/api/v1/components/%s/files/compose/BaseOS/x86_64/images/SHA256SUM"
        % rhel_81_component["id"]
    )
    assert r.status_code == 401

    r = client_admin.put(
        "/api/v1/teams/%s" % team1["id"],
        data={"has_pre_release_access": True},
        headers={"If-match": team1["etag"]},
    )
    assert r.status_code == 200

    r = hmac_client_team1.get(
        "/api/v1/components/%s/files/compose/BaseOS/x86_64/images/SHA256SUM"
        % rhel_81_component["id"]
    )
    assert r.status_code == 302

    s3_endpoint_url = dci_config.CONFIG["STORE_S3_ENDPOINT_URL"]
    bucket = dci_config.CONFIG["STORE_COMPONENTS_CONTAINER"]
    assert r.headers["Location"].startswith(
        f'{s3_endpoint_url}/{bucket}/{rhel_81_component["id"]}/compose/BaseOS/x86_64/images/SHA256SUM'
    )


def test_get_component_file_from_s3_user_team_in_RHEL81(
    client_admin,
    hmac_client_team1,
    team1,
    rhel_product,
    rhel_81_component,
):
    r = hmac_client_team1.get(
        "/api/v1/components/%s/files/COMPOSE_ID" % rhel_81_component["id"]
    )
    assert r.status_code == 401

    r = client_admin.post(
        "/api/v1/products/%s/teams" % rhel_product["id"],
        data={"team_id": team1["id"]},
    )
    assert r.status_code == 201

    r = client_admin.put(
        "/api/v1/teams/%s" % team1["id"],
        data={"has_pre_release_access": True},
        headers={"If-match": team1["etag"]},
    )
    assert r.status_code == 200

    r = hmac_client_team1.get(
        "/api/v1/components/%s/files/COMPOSE_ID" % rhel_81_component["id"]
    )
    assert r.status_code == 302

    s3_endpoint_url = dci_config.CONFIG["STORE_S3_ENDPOINT_URL"]
    bucket = dci_config.CONFIG["STORE_COMPONENTS_CONTAINER"]
    assert r.headers["Location"].startswith(
        f'{s3_endpoint_url}/{bucket}/{rhel_81_component["id"]}/COMPOSE_ID'
    )


def test_get_component_file_from_s3_return_400_if_transversal_attack(
    hmac_client_team1, rhel_80_component, rhel_81_component
):
    r = hmac_client_team1.get(
        "/api/v1/components/%s/files/COMPOSE_ID" % rhel_81_component["id"]
    )
    assert r.status_code == 401

    r = hmac_client_team1.get(
        "/api/v1/components/%s/files/COMPOSE_ID" % rhel_80_component["id"]
    )
    assert r.status_code == 302

    r = hmac_client_team1.get(
        "/api/v1/components/%s/files/../%s/COMPOSE_ID"
        % (rhel_80_component["id"], rhel_81_component["id"])
    )
    assert r.status_code == 400


def test_default_components_sort_is_by_released_at(client_admin, openshift_410_topic):
    r = client_admin.post(
        "/api/v1/components",
        data={
            "name": "OpenShift 4.10.50",
            "type": "ocp",
            "topic_id": openshift_410_topic["id"],
            "released_at": "2023-01-18T18:16:25.312257",
        },
    )
    assert r.status_code == 201
    r = client_admin.post(
        "/api/v1/components",
        data={
            "name": "OpenShift 4.10.49",
            "type": "ocp",
            "topic_id": openshift_410_topic["id"],
            "released_at": "2023-01-18T08:58:25.521351",
        },
    )
    assert r.status_code == 201
    components = client_admin.get(
        "/api/v1/topics/%s/components" % openshift_410_topic["id"],
    ).data["components"]
    assert components[0]["name"] == "OpenShift 4.10.50"
    assert components[1]["name"] == "OpenShift 4.10.49"


def test_get_components_without_any_permissions(
    client_admin,
    hmac_client_team1,
    rhel_81_component,
    rhel_80_component,
):
    r = hmac_client_team1.get("/api/v1/components")
    assert r.status_code == 200
    assert len(r.data["components"]) == 1
    assert r.data["components"][0]["id"] == rhel_80_component["id"]

    r = client_admin.get("/api/v1/components")
    assert r.status_code == 200
    components_ids = [c["id"] for c in r.data["components"]]
    assert components_ids == [rhel_80_component["id"], rhel_81_component["id"]]


def test_get_components_with_pre_release_access(
    client_admin,
    hmac_client_team1,
    team1,
    rhel_81_component,
    rhel_80_component,
):
    r = hmac_client_team1.get("/api/v1/components")
    assert r.status_code == 200
    assert len(r.data["components"]) == 1
    assert r.data["components"][0]["id"] == rhel_80_component["id"]

    r = client_admin.put(
        "/api/v1/teams/%s" % team1["id"],
        data={"has_pre_release_access": True},
        headers={"If-match": team1["etag"]},
    )
    assert r.status_code == 200

    r = hmac_client_team1.get("/api/v1/components")
    assert r.status_code == 200
    components_ids = [c["id"] for c in r.data["components"]]
    assert components_ids == [rhel_80_component["id"], rhel_81_component["id"]]


def test_get_components_sort(
    client_admin,
    rhel_81_component,
    rhel_80_component,
):
    r = client_admin.get("/api/v1/components?sort=-created_at")
    assert r.status_code == 200
    components_ids = [c["id"] for c in r.data["components"]]
    assert components_ids == [rhel_80_component["id"], rhel_81_component["id"]]

    r = client_admin.get("/api/v1/components?sort=created_at")
    assert r.status_code == 200
    components_ids = [c["id"] for c in r.data["components"]]
    assert components_ids == [rhel_81_component["id"], rhel_80_component["id"]]


def test_get_components_with_teams_component(
    hmac_client_team1,
    team1,
    rhel_80_topic,
    rhel_80_component,
):
    r = hmac_client_team1.get("/api/v1/components")
    assert r.status_code == 200
    assert len(r.data["components"]) == 1
    assert r.data["components"][0]["id"] == rhel_80_component["id"]

    data = {
        "name": "Kernel module",
        "type": "kernel_module",
        "topic_id": rhel_80_topic["id"],
        "team_id": team1["id"],
    }
    r = hmac_client_team1.post("/api/v1/components", data=data)
    assert r.status_code == 201
    team_component = r.data["component"]

    r = hmac_client_team1.get("/api/v1/components")
    assert r.status_code == 200
    components_ids = [c["id"] for c in r.data["components"]]
    assert components_ids == [team_component["id"], rhel_80_component["id"]]


def test_a_user_cant_access_another_user_component(
    client_user1, rhel_80_topic_id, team1_id, client_user2
):
    assert client_user1.get("/api/v1/components").data["components"] == []
    assert client_user2.get("/api/v1/components").data["components"] == []

    data = {
        "name": "Kernel module",
        "type": "kernel_module",
        "topic_id": rhel_80_topic_id,
        "team_id": team1_id,
    }
    r = client_user1.post("/api/v1/components", data=data)
    assert r.status_code == 201
    user_component = r.data["component"]

    r = client_user1.get("/api/v1/components")
    assert r.status_code == 200
    assert len(r.data["components"]) == 1
    assert r.data["components"][0]["id"] == user_component["id"]

    assert client_user2.get("/api/v1/components").data["components"] == []
