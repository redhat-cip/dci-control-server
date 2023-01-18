# -*- coding: utf-8 -*-
#
# Copyright (C) Red Hat, Inc
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
from datetime import datetime as dt
import mock
import pytest
import uuid
import time
from dci import dci_config
from dci.api.v1 import components
from dci.stores import files_utils
from dci.common import exceptions as dci_exc


@mock.patch("dci.api.v1.notifications.component_dispatcher")
def test_create_components_active(mock_disp, admin, topic_id):
    data = {
        "name": "pname",
        "type": "gerrit_review",
        "url": "http://example.com/",
        "topic_id": topic_id,
        "state": "active",
    }
    pc = admin.post("/api/v1/components", data=data).data
    pc_id = pc["component"]["id"]
    gc = admin.get("/api/v1/components/%s" % pc_id).data
    assert gc["component"]["name"] == "pname"
    assert gc["component"]["state"] == "active"
    mock_disp.assert_called()


@mock.patch("dci.api.v1.notifications.component_dispatcher")
def test_create_components_inactive(mock_disp, admin, topic_id):
    data = {
        "name": "pname",
        "type": "gerrit_review",
        "url": "http://example.com/",
        "topic_id": topic_id,
        "state": "inactive",
    }
    pc = admin.post("/api/v1/components", data=data).data
    pc_id = pc["component"]["id"]
    gc = admin.get("/api/v1/components/%s" % pc_id).data
    assert gc["component"]["name"] == "pname"
    assert gc["component"]["state"] == "inactive"
    mock_disp.assert_not_called()


def test_create_component_lowercase_type(admin, topic_id):
    data = {
        "name": "pname",
        "type": "GERRIT_REVIEW",
        "url": "http://example.com/",
        "topic_id": topic_id,
        "state": "active",
    }
    component = admin.post("/api/v1/components", data=data).data["component"]
    component = admin.get("/api/v1/components/%s" % component["id"]).data["component"]
    assert component["type"] == "gerrit_review"


def test_create_components_already_exist(admin, topic_user_id):
    data = {"name": "pname", "type": "gerrit_review", "topic_id": topic_user_id}
    pstatus_code = admin.post("/api/v1/components", data=data).status_code
    assert pstatus_code == 201

    pstatus_code = admin.post("/api/v1/components", data=data).status_code
    assert pstatus_code == 409


def test_create_components_with_same_name_on_different_topics(admin, topic_id, product):
    data = {"name": "pname", "type": "gerrit_review", "topic_id": topic_id}
    pstatus_code = admin.post("/api/v1/components", data=data).status_code
    assert pstatus_code == 201

    topic2 = admin.post(
        "/api/v1/topics",
        data={
            "name": "tname",
            "product_id": product["id"],
            "component_types": ["type1", "type2"],
        },
    ).data
    topic_id2 = topic2["topic"]["id"]

    data = {"name": "pname", "type": "gerrit_review", "topic_id": topic_id2}
    pstatus_code = admin.post("/api/v1/components", data=data).status_code
    assert pstatus_code == 201


def test_create_components_with_same_name_on_same_topics(admin, topic_user_id):
    data = {"name": "pname", "type": "gerrit_review", "topic_id": topic_user_id}
    pc1 = admin.post("/api/v1/components", data=data)
    assert pc1.status_code == 201

    pc2 = admin.post("/api/v1/components", data=data)
    assert pc2.status_code == 409


def test_create_components_with_same_name_on_same_topics_same_team(
    user, topic_user_id, team_user_id
):
    data = {
        "name": "pname",
        "type": "gerrit_review",
        "topic_id": topic_user_id,
        "team_id": team_user_id,
    }
    pstatus_code = user.post("/api/v1/components", data=data).status_code
    assert pstatus_code == 201

    pstatus_code = user.post("/api/v1/components", data=data).status_code
    assert pstatus_code == 409


def test_create_components_with_same_name_on_same_topics_different_team(
    user, user2, topic_user_id, team_user_id, team_user_id2
):
    data = {
        "name": "pname",
        "type": "gerrit_review",
        "topic_id": topic_user_id,
        "team_id": team_user_id,
    }
    pstatus_code = user.post("/api/v1/components", data=data).status_code
    assert pstatus_code == 201

    data = {
        "name": "pname",
        "type": "gerrit_review",
        "topic_id": topic_user_id,
        "team_id": team_user_id2,
    }
    pstatus_code = user2.post("/api/v1/components", data=data).status_code
    assert pstatus_code == 201


def test_recreate_components_with_same_name_on_same_topics(admin, topic_id):
    """The goal of this test is to verify that we can:
    - create a component, delete it, then create another component with
      the same name as the previous one
    - create, then delete, then create, then delete, multiple times a
      component with the same name
    """
    for n in range(3):
        data = {"name": "pouet", "type": "gerrit_review", "topic_id": topic_id}
        result = admin.post("/api/v1/components", data=data)
        assert result.status_code == 201

        result = admin.delete(
            "/api/v1/components/%s" % result.data["component"]["id"],
            headers={"If-match": result.data["component"]["etag"]},
        )
        assert result.status_code == 204


def test_create_components_with_same_name_and_different_type(admin, topic_id):
    data = {"name": "pname", "type": "first_type", "topic_id": topic_id}
    pstatus_code = admin.post("/api/v1/components", data=data).status_code
    assert pstatus_code == 201

    data = {"name": "pname", "type": "second_type", "topic_id": topic_id}
    pstatus_code = admin.post("/api/v1/components", data=data).status_code
    assert pstatus_code == 201


def test_create_component_with_tags(admin, topic_id):
    data = {
        "name": "pname",
        "type": "first_type",
        "topic_id": topic_id,
        "tags": ["tag1", "tag2"],
    }
    r = admin.post("/api/v1/components", data=data)
    assert r.status_code == 201

    component = r.data["component"]
    r = admin.get("/api/v1/components/%s" % component["id"])
    assert r.status_code == 200
    assert r.data["component"]["tags"] == ["tag1", "tag2"]

    r = admin.put(
        "/api/v1/components/%s" % component["id"],
        data={"state": "inactive"},
        headers={"If-match": component["etag"]},
    )
    assert r.status_code == 200
    assert r.data["component"]["tags"] == ["tag1", "tag2"]


def test_create_component_with_release_at(admin, topic_id):
    released_at = dt.utcnow().isoformat()
    data = {
        "name": "pname",
        "type": "first_type",
        "topic_id": topic_id,
        "released_at": released_at,
    }
    cmpt = admin.post("/api/v1/components", data=data)
    assert cmpt.status_code == 201

    cmpt = admin.get("/api/v1/components/%s" % cmpt.data["component"]["id"])
    assert cmpt.status_code == 200

    assert cmpt.data["component"]["released_at"] == released_at


def test_get_all_components_created_after(admin, topic_id):
    created_after = int(time.time() * 1000)
    for i in range(5):
        admin.post(
            "/api/v1/components",
            data={
                "name": "pname%s" % uuid.uuid4(),
                "type": "gerrit_review",
                "topic_id": topic_id,
            },
        ).data
    db_all_cs = admin.get(
        "/api/v1/topics/%s/components?created_after=%s&sort=created_at"
        % (topic_id, created_after)
    ).data
    assert len(db_all_cs["components"]) == 5
    component_2 = db_all_cs["components"][2]

    created_after = int(time.time() * 1000)
    db_all_cs = admin.get(
        "/api/v1/topics/%s/components?created_after=%s&sort=created_at"
        % (topic_id, created_after)
    ).data
    assert len(db_all_cs["components"]) == 0

    created_after = component_2["created_at"]
    db_all_cs = admin.get(
        "/api/v1/topics/%s/components?created_after=%s&sort=created_at"
        % (topic_id, created_after)
    ).data
    assert len(db_all_cs["components"]) == 3


def test_get_all_components_updated_after(admin, topic_id):
    for i in range(5):
        admin.post(
            "/api/v1/components",
            data={
                "name": "pname%s" % uuid.uuid4(),
                "type": "gerrit_review",
                "topic_id": topic_id,
            },
        ).data
    db_all_cs = admin.get(
        "/api/v1/topics/%s/components?sort=created_at" % topic_id
    ).data
    assert len(db_all_cs["components"]) == 5
    component_2 = db_all_cs["components"][2]

    updated_after = dt.utcnow().isoformat()
    db_all_cs = admin.get(
        "/api/v1/topics/%s/components?updated_after=%s&sort=created_at"
        % (topic_id, updated_after)
    ).data
    assert len(db_all_cs["components"]) == 0

    admin.put(
        "/api/v1/components/%s" % component_2["id"],
        headers={"If-match": component_2["etag"]},
        data={"name": "lol"},
    )
    component_2 = admin.get("/api/v1/components/%s" % component_2["id"])
    updated_after = component_2.data["component"]["updated_at"]
    db_all_cs = admin.get(
        "/api/v1/topics/%s/components?updated_after=%s&sort=created_at"
        % (topic_id, updated_after)
    ).data
    assert len(db_all_cs["components"]) == 1


def test_get_all_components(admin, topic_id):
    created_c_ids = []
    for i in range(5):
        pc = admin.post(
            "/api/v1/components",
            data={
                "name": "pname%s" % uuid.uuid4(),
                "type": "gerrit_review",
                "topic_id": topic_id,
            },
        ).data
        created_c_ids.append(pc["component"]["id"])
    created_c_ids.sort()

    db_all_cs = admin.get("/api/v1/topics/%s/components" % topic_id).data
    db_all_cs = db_all_cs["components"]
    db_all_cs_ids = [db_ct["id"] for db_ct in db_all_cs]
    db_all_cs_ids.sort()

    assert db_all_cs_ids == created_c_ids


def test_get_all_components_not_in_topic(admin, user, product_openstack):
    topic = admin.post(
        "/api/v1/topics",
        data={
            "name": "topic_test",
            "product_id": product_openstack["id"],
            "component_types": ["type1", "type2"],
        },
    ).data
    topic_id = topic["topic"]["id"]
    res = user.get("/api/v1/topics/%s/components" % topic_id)
    assert res.status_code == 401
    assert res.data["message"] == "Operation not authorized."


def test_get_all_components_with_pagination(admin, topic_id):
    # create 20 component types and check meta data count
    for i in range(20):
        admin.post(
            "/api/v1/components",
            data={
                "name": "pname%s" % uuid.uuid4(),
                "type": "gerrit_review",
                "topic_id": topic_id,
            },
        )
    cs = admin.get("/api/v1/topics/%s/components" % topic_id).data
    assert cs["_meta"]["count"] == 20

    # verify limit and offset are working well
    for i in range(4):
        cs = admin.get(
            "/api/v1/topics/%s/components?limit=5&offset=%s" % (topic_id, (i * 5))
        ).data
        assert len(cs["components"]) == 5

    # if offset is out of bound, the api returns an empty list
    cs = admin.get("/api/v1/topics/%s/components?limit=5&offset=300" % topic_id)
    assert cs.status_code == 200
    assert cs.data["components"] == []


def test_get_all_components_with_where(admin, topic_id):

    pc = admin.post(
        "/api/v1/components",
        data={"name": "pname1", "type": "gerrit_review", "topic_id": topic_id},
    ).data
    pc_id = pc["component"]["id"]
    admin.post(
        "/api/v1/components",
        data={"name": "pname2", "type": "gerrit_review", "topic_id": topic_id},
    ).data

    db_c = admin.get(
        "/api/v1/topics/%s/components?where=id:%s" % (topic_id, pc_id)
    ).data
    db_c_id = db_c["components"][0]["id"]
    assert db_c_id == pc_id

    db_c = admin.get("/api/v1/topics/%s/components?where=name:pname1" % topic_id).data
    db_c_id = db_c["components"][0]["id"]
    assert db_c_id == pc_id
    assert db_c["_meta"]["count"] == 1

    db_c = admin.get(
        "/api/v1/topics/%s/components?query=eq(name,pname1)" % topic_id
    ).data
    assert db_c["_meta"]["count"] == 1
    db_c_id = db_c["components"][0]["id"]
    assert db_c_id == pc_id

    db_c = admin.get(
        "/api/v1/topics/%s/components?query=and(eq(name,pname1),null(url))" % topic_id
    ).data
    assert db_c["_meta"]["count"] == 1
    db_c_id = db_c["components"][0]["id"]
    assert db_c_id == pc_id

    db_c = admin.get(
        "/api/v1/topics/%s/components?query=and(eq(name,pname1),not(null(url)))"
        % topic_id
    ).data
    print(db_c["components"])
    assert db_c["_meta"]["count"] == 0

    db_c = admin.get(
        "/api/v1/topics/%s/components?query=and(eq(name,pname1),eq(type,gerrit_review),eq(topic_id,%s))"
        % (topic_id, topic_id)
    ).data
    db_c_id = db_c["components"][0]["id"]
    assert db_c_id == pc_id
    assert db_c["_meta"]["count"] == 1


def test_nrt_get_all_components_with_new_line_in_where(admin, topic_id):
    response = admin.get(
        "/api/v1/topics/%s/components?sort=-created_at&where=name:RHOS-16.2-RHEL-8-20221005.n.1-\nASYNC,type:compose,state:active&limit=1&offset=0"
        % topic_id
    )
    assert response.status_code == 200


def test_where_invalid(admin, topic_id):
    err = admin.get("/api/v1/topics/%s/components?where=id" % topic_id)

    assert err.status_code == 400
    assert err.data["message"] == "Request malformed"
    assert err.data["payload"]["error"] == "where: 'id' is not a 'key value csv'"


def test_get_component_by_id_or_name(admin, topic_id):
    data = {
        "name": "pname",
        "type": "gerrit_review",
        "topic_id": topic_id,
    }
    pc = admin.post("/api/v1/components", data=data).data
    pc_id = pc["component"]["id"]

    # get by uuid
    created_ct = admin.get("/api/v1/components/%s" % pc_id)
    assert created_ct.status_code == 200

    created_ct = created_ct.data
    assert created_ct["component"]["id"] == pc_id


def test_nrt_get_component_by_id_return_list_of_jobs_only_from_team_of_the_user(
    job_admin, admin, user
):
    component = admin.get("/api/v1/jobs/%s" % job_admin["id"]).data["job"][
        "components"
    ][0]

    assert len(user.get("/api/v1/jobs").data["jobs"]) == 0
    assert (
        len(
            user.get("/api/v1/components/%s" % component["id"]).data["component"][
                "jobs"
            ]
        )
        == 0
    )


def test_nrt_get_component_by_id_return_list_of_jobs_if_rh_employee(
    job_admin, admin, rh_employee
):
    component = admin.get("/api/v1/jobs/%s" % job_admin["id"]).data["job"][
        "components"
    ][0]

    assert len(rh_employee.get("/api/v1/jobs").data["jobs"]) == 1
    jobs = rh_employee.get("/api/v1/components/%s" % component["id"]).data["component"][
        "jobs"
    ]
    assert len(jobs) == 1
    assert jobs[0]["id"] == job_admin["id"]


def test_get_component_not_found(admin):
    result = admin.get("/api/v1/components/ptdr")
    assert result.status_code == 404


def test_delete_component_by_id(admin, feeder_context, topic_user_id):

    data = {"name": "pname", "type": "gerrit_review", "topic_id": topic_user_id}
    pc = feeder_context.post("/api/v1/components", data=data)
    pc_id = pc.data["component"]["id"]
    assert pc.status_code == 201

    created_ct = admin.get("/api/v1/components/%s" % pc_id)
    assert created_ct.status_code == 200

    deleted_ct = admin.delete(
        "/api/v1/components/%s" % pc_id,
        headers={"If-match": pc.data["component"]["etag"]},
    )
    assert deleted_ct.status_code == 204

    gct = admin.get("/api/v1/components/%s" % pc_id)
    assert gct.status_code == 404


def test_get_all_components_with_sort(admin, topic_id):
    # create 4 components ordered by created time
    data = {
        "name": "pname1",
        "title": "aaa",
        "type": "gerrit_review",
        "topic_id": topic_id,
    }
    ct_1_1 = admin.post("/api/v1/components", data=data).data["component"]
    data = {
        "name": "pname2",
        "title": "aaa",
        "type": "gerrit_review",
        "topic_id": topic_id,
    }
    ct_1_2 = admin.post("/api/v1/components", data=data).data["component"]
    data = {
        "name": "pname3",
        "title": "bbb",
        "type": "gerrit_review",
        "topic_id": topic_id,
    }
    ct_2_1 = admin.post("/api/v1/components", data=data).data["component"]
    data = {
        "name": "pname4",
        "title": "bbb",
        "type": "gerrit_review",
        "topic_id": topic_id,
    }
    ct_2_2 = admin.post("/api/v1/components", data=data).data["component"]

    cts = admin.get("/api/v1/topics/%s/components?sort=created_at" % topic_id).data
    cts_id = [db_cts["id"] for db_cts in cts["components"]]
    assert cts_id == [ct_1_1["id"], ct_1_2["id"], ct_2_1["id"], ct_2_2["id"]]

    # sort by title first and then reverse by created_at
    cts = admin.get(
        "/api/v1/topics/%s/components?sort=title,-created_at" % topic_id
    ).data
    cts_id = [db_cts["id"] for db_cts in cts["components"]]
    assert cts_id == [ct_1_2["id"], ct_1_1["id"], ct_2_2["id"], ct_2_1["id"]]


def test_delete_component_not_found(admin):
    result = admin.delete(
        "/api/v1/components/%s" % uuid.uuid4(), headers={"If-match": "mdr"}
    )
    assert result.status_code == 404


def test_put_component(admin, user, topic_id):
    data = {
        "name": "pname1",
        "title": "aaa",
        "type": "gerrit_review",
        "topic_id": topic_id,
    }

    ct_1 = admin.post("/api/v1/components", data=data).data["component"]

    # Active component
    url = "/api/v1/components/%s" % ct_1["id"]
    data = {"name": "cname2"}
    headers = {"If-match": ct_1["etag"]}
    admin.put(url, data=data, headers=headers)

    ct_2 = admin.get("/api/v1/components/%s" % ct_1["id"]).data["component"]

    assert ct_1["etag"] != ct_2["etag"]
    assert ct_2["name"] == "cname2"


@mock.patch("dci.api.v1.notifications.component_dispatcher")
def test_put_component_from_inactive_to_active(mock_disp, admin, user, topic_id):
    data = {
        "name": "pname1",
        "title": "aaa",
        "type": "gerrit_review",
        "topic_id": topic_id,
        "state": "inactive",
    }

    ct_1 = admin.post("/api/v1/components", data=data).data["component"]
    mock_disp.assert_not_called()

    url = "/api/v1/components/%s" % ct_1["id"]
    data = {"name": "cname2", "state": "active"}
    headers = {"If-match": ct_1["etag"]}
    admin.put(url, data=data, headers=headers)
    mock_disp.assert_called()


def test_update_component_with_tags(admin, topic_id):
    data = {
        "name": "pname",
        "type": "first_type",
        "topic_id": topic_id,
        "tags": ["tag1", "tag2"],
    }
    cmpt = admin.post("/api/v1/components", data=data)
    assert cmpt.status_code == 201

    etag = cmpt.data["component"]["etag"]
    data = {"tags": ["hihi", "haha"]}
    admin.put(
        "/api/v1/components/%s" % cmpt.data["component"]["id"],
        data=data,
        headers={"If-match": etag},
    )

    cmpt = admin.get("/api/v1/components/%s" % cmpt.data["component"]["id"])
    assert cmpt.data["component"]["tags"] == ["hihi", "haha"]


def test_update_component_lowercase_type(admin, topic_id):
    data = {
        "name": "pname",
        "type": "GERRIT_REVIEW",
        "url": "http://example.com/",
        "topic_id": topic_id,
        "state": "active",
    }
    component = admin.post("/api/v1/components", data=data).data["component"]
    component = admin.put(
        "/api/v1/components/%s" % component["id"],
        data={"type": "METADATA"},
        headers={"If-match": component["etag"]},
    ).data["component"]
    assert component["type"] == "metadata"


def test_add_file_to_component(admin, topic_id):
    def create_ct(name):
        data = {
            "name": name,
            "title": "aaa",
            "type": "gerrit_review",
            "topic_id": topic_id,
        }
        return admin.post("/api/v1/components", data=data).data["component"]

    ct_1 = create_ct("pname1")
    ct_2 = create_ct("pname2")

    cts = admin.get("/api/v1/components/%s?embed=files" % ct_1["id"]).data
    assert len(cts["component"]["files"]) == 0

    url = "/api/v1/components/%s/files" % ct_1["id"]
    c_file = admin.post(url, data="lol")
    c_file_1_id = c_file.data["component_file"]["id"]
    url = "/api/v1/components/%s/files" % ct_2["id"]
    c_file = admin.post(url, data="lol2")
    c_file_2_id = c_file.data["component_file"]["id"]

    assert c_file.status_code == 201
    l_file = admin.get(url)
    assert l_file.status_code == 200
    assert l_file.data["_meta"]["count"] == 1
    assert l_file.data["component_files"][0]["component_id"] == ct_2["id"]
    cts = admin.get("/api/v1/components/%s?embed=files" % ct_1["id"]).data
    assert len(cts["component"]["files"]) == 1
    assert cts["component"]["files"][0]["size"] == 5

    cts = admin.get("/api/v1/components/%s/files" % ct_1["id"]).data
    assert cts["component_files"][0]["id"] == c_file_1_id

    cts = admin.get("/api/v1/components/%s/files" % ct_2["id"]).data
    assert cts["component_files"][0]["id"] == c_file_2_id


def test_download_file_from_component(admin, topic_id):
    data = {
        "name": "pname1",
        "title": "aaa",
        "type": "gerrit_review",
        "topic_id": topic_id,
    }
    ct_1 = admin.post("/api/v1/components", data=data).data["component"]

    url = "/api/v1/components/%s/files" % ct_1["id"]
    data = "lollollel"
    c_file = admin.post(url, data=data).data["component_file"]

    url = "/api/v1/components/%s/files/%s/content" % (ct_1["id"], c_file["id"])
    d_file = admin.get(url)
    assert d_file.status_code == 200
    assert d_file.data == '"lollollel"'


def test_delete_file_from_component(admin, topic_id):
    data = {
        "name": "pname1",
        "title": "aaa",
        "type": "gerrit_review",
        "topic_id": topic_id,
    }
    ct_1 = admin.post("/api/v1/components", data=data).data["component"]

    url = "/api/v1/components/%s/files" % ct_1["id"]
    data = "lol"
    c_file = admin.post(url, data=data).data["component_file"]
    url = "/api/v1/components/%s/files" % ct_1["id"]
    g_files = admin.get(url)
    assert g_files.data["_meta"]["count"] == 1

    url = "/api/v1/components/%s/files/%s" % (ct_1["id"], c_file["id"])
    d_file = admin.delete(url, headers={"If-match": c_file["etag"]})
    assert d_file.status_code == 204

    url = "/api/v1/components/%s/files" % ct_1["id"]
    g_files = admin.get(url)
    assert g_files.data["_meta"]["count"] == 0


def test_change_component_state(admin, topic_id):
    data = {
        "name": "pname",
        "type": "gerrit_review",
        "url": "http://example.com/",
        "topic_id": topic_id,
        "state": "active",
    }
    pc = admin.post("/api/v1/components", data=data).data
    pc_id = pc["component"]["id"]

    t = admin.get("/api/v1/components/" + pc_id).data["component"]
    data = {"state": "inactive"}
    r = admin.put(
        "/api/v1/components/" + pc_id, data=data, headers={"If-match": t["etag"]}
    )
    assert r.status_code == 200
    assert r.data["component"]["state"] == "inactive"


def test_change_component_to_invalid_state(admin, topic_id):
    data = {
        "name": "pname",
        "type": "gerrit_review",
        "url": "http://example.com/",
        "topic_id": topic_id,
        "state": "active",
    }
    pc = admin.post("/api/v1/components", data=data).data
    pc_id = pc["component"]["id"]

    t = admin.get("/api/v1/components/" + pc_id).data["component"]
    data = {"state": "kikoolol"}
    r = admin.put(
        "/api/v1/components/" + pc_id, data=data, headers={"If-match": t["etag"]}
    )
    assert r.status_code == 400
    current_component = admin.get("/api/v1/components/" + pc_id)
    assert current_component.status_code == 200
    assert current_component.data["component"]["state"] == "active"


def test_component_success_update_field_by_field(admin, topic_id):
    data = {"name": "pname", "type": "gerrit_review", "topic_id": topic_id}
    c = admin.post("/api/v1/components", data=data).data["component"]

    admin.put(
        "/api/v1/components/%s" % c["id"],
        data={"state": "inactive"},
        headers={"If-match": c["etag"]},
    )

    c = admin.get("/api/v1/components/%s" % c["id"]).data["component"]

    assert c["name"] == "pname"
    assert c["state"] == "inactive"
    assert c["title"] is None

    c = admin.put(
        "/api/v1/components/%s" % c["id"],
        data={"name": "pname2"},
        headers={"If-match": c["etag"]},
    ).data["component"]

    assert c["name"] == "pname2"
    assert c["state"] == "inactive"
    assert c["title"] is None

    admin.put(
        "/api/v1/components/%s" % c["id"],
        data={"title": "a new title"},
        headers={"If-match": c["etag"]},
    )

    c = admin.get("/api/v1/components/%s" % c["id"]).data["component"]

    assert c["name"] == "pname2"
    assert c["state"] == "inactive"
    assert c["title"] == "a new title"


def create_component(admin, topic_id, ct, name):
    data = {"topic_id": topic_id, "name": name, "type": ct}
    component = admin.post("/api/v1/components", data=data).data
    return str(component["component"]["id"])


def test_get_last_components_by_type(session, admin, topic):

    components_ids = []
    for i in range(3):
        cid = create_component(admin, topic["id"], "puddle_osp", "name-%s" % i)
        components_ids.append(cid)

    last_components = components.get_last_components_by_type(
        ["puddle_osp"], topic_id=topic["id"], session=session
    )
    assert str(last_components[0].id) == components_ids[-1]


def test_verify_and_get_components_ids(session, admin, topic, topic_user_id):
    # components types not valid
    with pytest.raises(dci_exc.DCIException):
        components.verify_and_get_components_ids(
            topic["id"], [], ["puddle_osp"], session=session
        )

    with pytest.raises(dci_exc.DCIException):
        components.verify_and_get_components_ids(
            topic["id"],
            [str(uuid.uuid4())],
            ["puddle_osp"],
            session=session,
        )

    # duplicated component types
    c1 = create_component(admin, topic_user_id, "type1", "n1")
    c2 = create_component(admin, topic_user_id, "type1", "n2")
    c3 = create_component(admin, topic_user_id, "type2", "n3")
    with pytest.raises(dci_exc.DCIException):
        components.verify_and_get_components_ids(
            topic_user_id,
            [c1, c2, c3],
            ["type_1", "type_2", "type_3"],
            session=session,
        )

    cids = components.verify_and_get_components_ids(
        topic_user_id,
        [c1, c3],
        ["type_1", "type_2"],
        session=session,
    )
    assert set(cids) == {c1, c3}


def test_purge(admin, components_user_ids, topic_user_id):
    component_id = components_user_ids[0]
    store = dci_config.get_store()

    url = "/api/v1/components/%s/files" % component_id
    c_file1 = admin.post(url, data="lol")
    assert c_file1.status_code == 201

    path1 = files_utils.build_file_path(
        topic_user_id, component_id, c_file1.data["component_file"]["id"]
    )
    store.get("components", path1)

    url = "/api/v1/components/%s/files" % component_id
    c_file2 = admin.post(url, data="lol")
    assert c_file2.status_code == 201

    path2 = files_utils.build_file_path(
        topic_user_id, component_id, c_file2.data["component_file"]["id"]
    )
    store.get("components", path2)

    component = admin.get("/api/v1/components/%s" % component_id).data["component"]
    admin.delete(
        "/api/v1/components/%s" % component_id, headers={"If-match": component["etag"]}
    )
    to_purge = admin.get("/api/v1/components/purge").data
    assert len(to_purge["components"]) == 1
    c_purged = admin.post("/api/v1/components/purge")
    assert c_purged.status_code == 204

    with pytest.raises(dci_exc.StoreException):
        store.get("components", path1)

    with pytest.raises(dci_exc.StoreException):
        store.get("components", path2)

    to_purge = admin.get("/api/v1/components/purge").data
    assert len(to_purge["components"]) == 0


def test_purge_failure(admin, components_user_ids, topic_user_id):
    component_id = components_user_ids[0]

    url = "/api/v1/components/%s/files" % component_id
    c_file1 = admin.post(url, data="lol")
    assert c_file1.status_code == 201

    c_files = admin.get("/api/v1/components/%s/files" % component_id)
    assert len(c_files.data["component_files"]) == 1

    component = admin.get("/api/v1/components/%s" % component_id).data["component"]
    d_component = admin.delete(
        "/api/v1/components/%s" % component_id, headers={"If-match": component["etag"]}
    )
    assert d_component.status_code == 204
    to_purge = admin.get("/api/v1/components/purge").data
    assert len(to_purge["components"]) == 1
    # purge will fail
    with mock.patch("dci.stores.s3.S3.delete") as mock_delete:
        path1 = files_utils.build_file_path(
            topic_user_id, component_id, c_file1.data["component_file"]["id"]
        )
        mock_delete.side_effect = dci_exc.StoreException("error")
        purge_res = admin.post("/api/v1/components/purge")
        assert purge_res.status_code == 400
        store = dci_config.get_store()
        store.get("components", path1)
        to_purge = admin.get("/api/v1/components/purge").data
        assert len(to_purge["components"]) == 1


def test_create_component_as_feeder(admin, topic_id, feeder_context):
    data = {"name": "c1", "type": "snapshot", "topic_id": topic_id, "state": "active"}
    c = feeder_context.post("/api/v1/components", data=data).data["component"]
    component = admin.get("/api/v1/components/%s" % c["id"]).data["component"]
    assert component["name"] == "c1"
    assert component["state"] == "active"


def test_update_component_as_feeder(admin, topic_id, feeder_context):
    data = {"name": "c1", "type": "snapshot", "topic_id": topic_id, "state": "active"}
    c = feeder_context.post("/api/v1/components", data=data).data["component"]
    feeder_context.put(
        "/api/v1/components/%s" % c["id"],
        data={"type": "tar"},
        headers={"If-match": c["etag"]},
    )
    component = admin.get("/api/v1/components/%s" % c["id"]).data["component"]
    assert component["name"] == "c1"
    assert component["type"] == "tar"


def test_create_component_not_allowed_for_user_and_remoteci(
    user, remoteci_context, topic_user_id
):
    data = {
        "name": "c1",
        "type": "snapshot",
        "topic_id": topic_user_id,
        "state": "active",
    }
    c = user.post("/api/v1/components", data=data)
    assert c.status_code == 401
    c = remoteci_context.post("/api/v1/components", data=data)
    assert c.status_code == 401


# ######### tests teams components


def test_create_teams_components(user, team_user_id, topic_user_id):
    data = {
        "name": "pname",
        "type": "gerrit_review",
        "url": "http://example.com/",
        "team_id": team_user_id,
        "topic_id": topic_user_id,
        "state": "active",
    }
    pc = user.post("/api/v1/components", data=data).data
    pc_id = pc["component"]["id"]

    gc = user.get("/api/v1/components/%s" % pc_id).data
    assert gc["component"]["name"] == "pname"
    assert gc["component"]["state"] == "active"


def test_get_all_teams_components(user, team_user_id, topic_user_id):
    data = {
        "name": "pname",
        "type": "gerrit_review",
        "url": "http://example.com/",
        "team_id": team_user_id,
        "topic_id": topic_user_id,
        "state": "active",
    }
    pc = user.post("/api/v1/components", data=data).data
    pc_id = pc["component"]["id"]
    cmpts = user.get(
        "/api/v1/topics/%s/components?where=team_id:%s" % (topic_user_id, team_user_id)
    ).data
    assert cmpts["components"][0]["id"] == pc_id


def test_update_teams_components(user, team_user_id, topic_user_id):
    data = {
        "name": "pname",
        "type": "gerrit_review",
        "url": "http://example.com/",
        "team_id": team_user_id,
        "topic_id": topic_user_id,
        "state": "active",
    }
    pc = user.post("/api/v1/components", data=data).data
    pc_id = pc["component"]["id"]
    etag = pc["component"]["etag"]
    user.put(
        "/api/v1/components/%s" % pc_id,
        data={"name": "pname2"},
        headers={"If-match": etag},
    )
    gc = user.get("/api/v1/components/%s" % pc_id).data
    assert gc["component"]["name"] == "pname2"


def test_delete_teams_components(user, team_user_id, topic_user_id):
    data = {
        "name": "pname",
        "type": "gerrit_review",
        "url": "http://example.com/",
        "team_id": team_user_id,
        "topic_id": topic_user_id,
        "state": "active",
    }
    pc = user.post("/api/v1/components", data=data).data
    pc_id = pc["component"]["id"]

    gc = user.get("/api/v1/components/%s" % pc_id)
    assert gc.status_code == 200

    gc = user.delete(
        "/api/v1/components/%s" % pc_id, headers={"If-match": pc["component"]["etag"]}
    )
    assert gc.status_code == 204

    gc = user.get("/api/v1/components/%s" % pc_id)
    assert gc.status_code == 404


def test_filter_teams_components_by_tag(user, team_user_id, topic_user_id):

    data = {
        "name": "pname",
        "type": "mytest",
        "team_id": team_user_id,
        "topic_id": topic_user_id,
        "tags": ["tag1", "common"],
    }
    user.post("/api/v1/components", data=data).data

    data = {
        "name": "pname",
        "type": "mylib",
        "team_id": team_user_id,
        "topic_id": topic_user_id,
        "tags": ["tag2", "common"],
    }
    user.post("/api/v1/components", data=data).data

    res = user.get(
        "/api/v1/topics/%s/components?where=tags:tag1,team_id:%s"
        % (topic_user_id, team_user_id)
    )
    assert len(res.data["components"]) == 1
    assert "tag1" in res.data["components"][0]["tags"]
    assert "tag2" not in res.data["components"][0]["tags"]

    res = user.get(
        "/api/v1/topics/%s/components?query=and(contains(tags,tag1),eq(team_id,%s))"
        % (topic_user_id, team_user_id)
    )
    assert len(res.data["components"]) == 1
    assert "tag1" in res.data["components"][0]["tags"]
    assert "tag2" not in res.data["components"][0]["tags"]

    res = user.get(
        "/api/v1/topics/%s/components?where=tags:common,team_id:%s"
        % (topic_user_id, team_user_id)
    )
    assert len(res.data["components"]) == 2
    assert "common" in res.data["components"][0]["tags"]
    assert "common" in res.data["components"][1]["tags"]


def test_teams_components_isolation(
    user, user2, topic_user_id, team_user_id, team_user_id2
):
    data = {
        "name": "pname",
        "type": "mytest",
        "topic_id": topic_user_id,
        "team_id": team_user_id,
    }
    pc = user.post("/api/v1/components", data=data)
    assert pc.status_code == 201

    components = user.get(
        "/api/v1/topics/%s/components?where=team_id:%s" % (topic_user_id, team_user_id)
    ).data
    assert components["components"][0]["team_id"] == team_user_id

    data = {
        "name": "pname",
        "type": "mytest",
        "topic_id": topic_user_id,
        "team_id": team_user_id2,
    }
    pc = user.post("/api/v1/components", data=data)
    assert pc.status_code == 401
    pc = user2.post("/api/v1/components", data=data)
    assert pc.status_code == 201

    components = user2.get(
        "/api/v1/topics/%s/components?where=team_id:%s" % (topic_user_id, team_user_id)
    )
    assert components.status_code == 200
    assert components.data["components"] == []
    components = user2.get(
        "/api/v1/topics/%s/components?where=team_id:%s" % (topic_user_id, team_user_id2)
    )
    assert components.status_code == 200
    assert components.data["components"][0]["team_id"] == team_user_id2


# S3 components related tests


def test_get_component_file_from_s3_user_team_in_RHEL_export_control_true(
    admin,
    remoteci_context,
    remoteci_user,
    RHELProduct,
    RHEL80Component,
):

    r = remoteci_context.get(
        "/api/v1/components/%s/files/.composeinfo" % RHEL80Component["id"]
    )
    assert r.status_code == 401

    r = remoteci_context.head(
        "/api/v1/components/%s/files/.composeinfo" % RHEL80Component["id"]
    )
    assert r.status_code == 401

    r = admin.post(
        "/api/v1/products/%s/teams" % RHELProduct["id"],
        data={"team_id": remoteci_user["team_id"]},
    )
    assert r.status_code == 201

    r = remoteci_context.get(
        "/api/v1/components/%s/files/.composeinfo" % RHEL80Component["id"]
    )
    assert r.status_code == 302

    s3_endpoint_url = dci_config.CONFIG["STORE_S3_ENDPOINT_URL"]
    bucket = dci_config.CONFIG["STORE_COMPONENTS_CONTAINER"]
    assert r.headers["Location"].startswith(
        f"{s3_endpoint_url}/{bucket}/{RHEL80Component['id']}/.composeinfo"
    )

    r = remoteci_context.head(
        "/api/v1/components/%s/files/.composeinfo" % RHEL80Component["id"]
    )
    assert r.status_code == 302
    assert r.headers["Location"].startswith(
        f"{s3_endpoint_url}/{bucket}/{RHEL80Component['id']}/.composeinfo"
    )


def test_get_component_file_from_s3_user_team_in_RHEL_export_control_false(
    admin,
    remoteci_context,
    remoteci_user,
    RHELProduct,
    RHEL81Topic,
    RHEL81Component,
):

    r = remoteci_context.get(
        "/api/v1/components/%s/files/compose/BaseOS/x86_64/images/SHA256SUM"
        % RHEL81Component["id"]
    )
    assert r.status_code == 401

    r = admin.post(
        "/api/v1/products/%s/teams" % RHELProduct["id"],
        data={"team_id": remoteci_user["team_id"]},
    )
    assert r.status_code == 201

    r = remoteci_context.get(
        "/api/v1/components/%s/files/compose/BaseOS/x86_64/images/SHA256SUM"
        % RHEL81Component["id"]
    )
    assert r.status_code == 401

    r = admin.post(
        "/api/v1/topics/%s/teams" % RHEL81Topic["id"],
        data={"team_id": remoteci_user["team_id"]},
    )
    assert r.status_code == 201

    r = remoteci_context.get(
        "/api/v1/components/%s/files/compose/BaseOS/x86_64/images/SHA256SUM"
        % RHEL81Component["id"]
    )
    assert r.status_code == 302

    s3_endpoint_url = dci_config.CONFIG["STORE_S3_ENDPOINT_URL"]
    bucket = dci_config.CONFIG["STORE_COMPONENTS_CONTAINER"]
    assert r.headers["Location"].startswith(
        f'{s3_endpoint_url}/{bucket}/{RHEL81Component["id"]}/compose/BaseOS/x86_64/images/SHA256SUM'
    )


def test_get_component_file_from_s3_user_team_in_RHEL81(
    admin,
    remoteci_context,
    remoteci_user,
    RHELProduct,
    RHEL81Topic,
    RHEL81Component,
):

    r = remoteci_context.get(
        "/api/v1/components/%s/files/COMPOSE_ID" % RHEL81Component["id"]
    )
    assert r.status_code == 401

    r = admin.post(
        "/api/v1/products/%s/teams" % RHELProduct["id"],
        data={"team_id": remoteci_user["team_id"]},
    )
    assert r.status_code == 201

    r = admin.post(
        "/api/v1/topics/%s/teams" % RHEL81Topic["id"],
        data={"team_id": remoteci_user["team_id"]},
    )
    assert r.status_code == 201

    r = remoteci_context.get(
        "/api/v1/components/%s/files/COMPOSE_ID" % RHEL81Component["id"]
    )
    assert r.status_code == 302

    s3_endpoint_url = dci_config.CONFIG["STORE_S3_ENDPOINT_URL"]
    bucket = dci_config.CONFIG["STORE_COMPONENTS_CONTAINER"]
    assert r.headers["Location"].startswith(
        f'{s3_endpoint_url}/{bucket}/{RHEL81Component["id"]}/COMPOSE_ID'
    )


def test_get_component_file_from_s3_return_400_if_transversal_attack(
    remoteci_context, topic_user_id, RHEL80Component
):
    r = remoteci_context.get(
        "/api/v1/components/%s/files/COMPOSE_ID" % RHEL80Component["id"]
    )
    assert r.status_code == 401

    component = remoteci_context.get(
        "/api/v1/topics/%s/components" % topic_user_id
    ).data["components"][0]
    r = remoteci_context.get("/api/v1/components/%s/files/COMPOSE_ID" % component["id"])
    assert r.status_code == 302

    r = remoteci_context.get(
        "/api/v1/components/%s/files/../%s/COMPOSE_ID"
        % (component["id"], RHEL80Component["id"])
    )
    assert r.status_code == 400


def test_default_components_sort_is_by_released_at(admin, openshift_410):
    r = admin.post(
        "/api/v1/components",
        data={
            "name": "OpenShift 4.10.50",
            "type": "ocp",
            "topic_id": openshift_410["id"],
            "released_at": "2023-01-18T18:16:25.312257",
        },
    )
    assert r.status_code == 201
    r = admin.post(
        "/api/v1/components",
        data={
            "name": "OpenShift 4.10.49",
            "type": "ocp",
            "topic_id": openshift_410["id"],
            "released_at": "2023-01-18T08:58:25.521351",
        },
    )
    assert r.status_code == 201
    components = admin.get(
        "/api/v1/topics/%s/components" % openshift_410["id"],
    ).data["components"]
    assert components[0]["name"] == "OpenShift 4.10.50"
    assert components[1]["name"] == "OpenShift 4.10.49"
