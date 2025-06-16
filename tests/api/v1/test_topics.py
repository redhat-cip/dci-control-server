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
import uuid


def topic_creation(identity, product):
    data = {
        "name": "tname",
        "product_id": product["id"],
        "component_types": ["type1", "type2"],
    }
    pt = identity.post("/api/v1/topics", data=data).data
    pt_id = pt["topic"]["id"]
    return identity.get("/api/v1/topics/%s" % pt_id)


def topic_update(identity, topic_id):
    t = identity.get("/api/v1/topics/" + topic_id).data["topic"]
    data = {"component_types": ["lol1", "lol2"], "data": {"foo": "bar"}}
    identity.put(
        "/api/v1/topics/" + topic_id, data=data, headers={"If-match": t["etag"]}
    )

    return identity.get("/api/v1/topics/" + topic_id)


def topic_removal(identity, topic_id, etag):
    return identity.delete("/api/v1/topics/%s" % topic_id, headers={"If-match": etag})


def test_create_topics(client_admin, rhel_product):
    topic = topic_creation(client_admin, rhel_product).data
    assert topic["topic"]["name"] == "tname"
    assert topic["topic"]["component_types"] == ["type1", "type2"]


def test_topic_creation_with_opts(client_admin, rhel_product):
    data = {
        "name": "tname",
        "product_id": rhel_product["id"],
        "component_types": ["type1", "type2"],
        "component_types_optional": ["type3"],
        "data": {"foo": "bar"},
    }
    pt = client_admin.post("/api/v1/topics", data=data).data
    pt_id = pt["topic"]["id"]
    t = client_admin.get("/api/v1/topics/%s" % pt_id).data
    assert t["topic"]["data"]["foo"] == "bar"
    assert t["topic"]["component_types_optional"] == ["type3"]


def test_create_topic_as_feeder(hmac_client_feeder, rhel_product):
    topic = topic_creation(hmac_client_feeder, rhel_product).data
    assert topic["topic"]["name"] == "tname"
    assert topic["topic"]["component_types"] == ["type1", "type2"]


def test_create_topics_as_user(client_user1, rhel_product):
    data = {
        "name": "tname",
        "product_id": rhel_product["id"],
        "component_types": ["type1", "type2"],
    }
    status_code = client_user1.post("/api/v1/topics", data=data).status_code
    assert status_code == 401


def test_create_topic_lowercase_component_types(client_admin, rhel_product):
    data = {
        "name": "tname",
        "product_id": rhel_product["id"],
        "component_types": ["tYpe1", "Type2"],
    }
    topic = client_admin.post("/api/v1/topics", data=data).data["topic"]
    topic = client_admin.get("/api/v1/topics/%s" % topic["id"]).data["topic"]
    assert topic["component_types"] == ["type1", "type2"]


def test_update_topics_as_admin(client_admin, rhel_80_topic_id):
    topic = topic_update(client_admin, rhel_80_topic_id).data["topic"]
    assert topic["component_types"] == ["lol1", "lol2"]
    assert topic["data"]["foo"] == "bar"


def test_update_topic_as_feeder(hmac_client_feeder, rhel_80_topic_id):
    topic = topic_update(hmac_client_feeder, rhel_80_topic_id).data["topic"]
    assert topic["component_types"] == ["lol1", "lol2"]
    assert topic["data"]["foo"] == "bar"


def test_update_topic_lowercase_component_types(client_admin, rhel_product):
    data = {
        "name": "tname",
        "product_id": rhel_product["id"],
    }
    topic = client_admin.post("/api/v1/topics", data=data).data["topic"]
    topic = client_admin.put(
        "/api/v1/topics/%s" % topic["id"],
        data={"component_types": ["tYpe1", "Type2"]},
        headers={"If-match": topic["etag"]},
    ).data["topic"]
    topic = client_admin.get("/api/v1/topics/%s" % topic["id"]).data["topic"]
    assert topic["component_types"] == ["type1", "type2"]


def test_change_topic_state(client_admin, rhel_80_topic_id):
    t = client_admin.get("/api/v1/topics/" + rhel_80_topic_id).data["topic"]
    data = {"state": "inactive"}
    r = client_admin.put(
        "/api/v1/topics/" + rhel_80_topic_id, data=data, headers={"If-match": t["etag"]}
    )
    assert r.status_code == 200
    assert r.data["topic"]["state"] == "inactive"


def test_change_topic_to_invalid_state(client_admin, rhel_80_topic_id):
    t = client_admin.get("/api/v1/topics/" + rhel_80_topic_id).data["topic"]
    data = {"state": "kikoolol"}
    r = client_admin.put(
        "/api/v1/topics/" + rhel_80_topic_id, data=data, headers={"If-match": t["etag"]}
    )
    assert r.status_code == 400
    current_topic = client_admin.get("/api/v1/topics/" + rhel_80_topic_id)
    assert current_topic.status_code == 200
    assert current_topic.data["topic"]["state"] == "active"


def test_create_topics_already_exist(client_admin, rhel_product):
    data = {
        "name": "tname",
        "product_id": rhel_product["id"],
        "component_types": ["type1", "type2"],
    }
    pstatus_code = client_admin.post("/api/v1/topics", data=data).status_code
    assert pstatus_code == 201

    data = {
        "name": "tname",
        "product_id": rhel_product["id"],
        "component_types": ["type1", "type2"],
    }
    pstatus_code = client_admin.post("/api/v1/topics", data=data).status_code
    assert pstatus_code == 409


def test_get_all_topics_by_admin(client_admin, rhel_product):
    created_topics_ids = []
    for i in range(5):
        pc = client_admin.post(
            "/api/v1/topics",
            data={
                "name": "tname%s" % uuid.uuid4(),
                "product_id": rhel_product["id"],
                "component_types": ["type1", "type2"],
            },
        ).data
        created_topics_ids.append(pc["topic"]["id"])
    created_topics_ids.sort()

    db_all_cs = client_admin.get("/api/v1/topics").data
    db_all_cs = db_all_cs["topics"]
    db_all_cs_ids = [db_ct["id"] for db_ct in db_all_cs]
    db_all_cs_ids.sort()

    assert db_all_cs_ids == created_topics_ids


def test_get_all_topics_by_user_and_remoteci(
    client_admin, client_user1, hmac_client_team1, team1_id, rhel_product
):
    pat = client_admin.post(
        "/api/v1/products/%s/teams" % rhel_product["id"], data={"team_id": team1_id}
    )
    assert pat.status_code == 201

    def test(caller, topic_name):
        # create a topic with export_control==False
        my_topic = client_admin.post(
            "/api/v1/topics",
            data={
                "name": topic_name,
                "product_id": rhel_product["id"],
                "export_control": False,
                "component_types": ["type1", "type2"],
            },
        )
        assert my_topic.status_code == 201
        my_topic_id = my_topic.data["topic"]["id"]
        my_topic_etag = my_topic.data["topic"]["etag"]

        team_user = client_admin.get("/api/v1/teams/%s" % team1_id).data["team"]
        assert team_user["has_pre_release_access"] is False

        # user should not find it
        my_topic = caller.get("/api/v1/topics?where=name:%s" % topic_name)
        assert len(my_topic.data["topics"]) == 0

        # allow team to access pre release content
        assert (
            client_admin.put(
                "/api/v1/teams/%s" % team_user["id"],
                data={"has_pre_release_access": True},
                headers={"If-match": team_user["etag"]},
            ).status_code
            == 200
        )

        # user should see the topic now
        my_topic = caller.get("/api/v1/topics?where=name:%s" % topic_name)
        assert my_topic.data["topics"][0]["name"] == topic_name

        # remove team permission
        team_user = client_admin.get("/api/v1/teams/%s" % team1_id).data["team"]
        assert (
            client_admin.put(
                "/api/v1/teams/%s" % team_user["id"],
                data={"has_pre_release_access": False},
                headers={"If-match": team_user["etag"]},
            ).status_code
            == 200
        )

        # user should not find it
        my_topic = caller.get("/api/v1/topics?where=name:%s" % topic_name)
        assert len(my_topic.data["topics"]) == 0

        # update export_control to True
        client_admin.put(
            "/api/v1/topics/%s" % my_topic_id,
            headers={"If-match": my_topic_etag},
            data={"export_control": True},
        )

        # user should see the topic now
        my_topic = caller.get("/api/v1/topics?where=name:%s" % topic_name)
        assert my_topic.data["topics"][0]["name"] == topic_name

    test(client_user1, "my_new_topic_1")
    test(hmac_client_team1, "my_new_topic_2")


def test_get_all_topics_with_pagination(client_admin, rhel_product):
    cs = client_admin.get("/api/v1/topics").data
    nb_topics_init = cs["_meta"]["count"]

    # create 20 topic types and check meta data count
    for i in range(20):
        client_admin.post(
            "/api/v1/topics",
            data={
                "name": "tname%s" % uuid.uuid4(),
                "product_id": rhel_product["id"],
                "component_types": ["type1", "type2"],
            },
        )
    cs = client_admin.get("/api/v1/topics").data
    assert cs["_meta"]["count"] == nb_topics_init + 20

    # verify limit and offset are working well
    for i in range(4):
        cs = client_admin.get("/api/v1/topics?limit=5&offset=%s" % (i * 5)).data
        assert len(cs["topics"]) == 5

    # if offset is out of bound, the api returns an empty list
    cs = client_admin.get("/api/v1/topics?limit=5&offset=300")
    assert cs.status_code == 200
    assert cs.data["topics"] == []


def test_get_all_topics_with_where(client_admin, rhel_product):
    # create 20 topic types and check meta data count
    topics = {}
    for i in range(20):
        t_name = str(uuid.uuid4())
        r = client_admin.post(
            "/api/v1/topics",
            data={
                "name": t_name,
                "product_id": rhel_product["id"],
                "component_types": ["type1", "type2"],
            },
        ).data
        topics[t_name] = r["topic"]["id"]

    for t_name, t_id in topics.items():
        r = client_admin.get(
            "/api/v1/topics?where=name:%s&limit=1&offset=0" % t_name
        ).data
        assert r["_meta"]["count"] == 1
        assert r["topics"][0]["id"] == t_id


def test_get_topic_by_id(client_admin, client_user1, rhel_product):
    data = {
        "name": "tname",
        "product_id": rhel_product["id"],
        "component_types": ["type1", "type2"],
        "export_control": True,
    }
    pt = client_admin.post("/api/v1/topics", data=data).data
    pt_id = pt["topic"]["id"]

    # get by uuid
    created_ct = client_user1.get("/api/v1/topics/%s" % pt_id)
    assert created_ct.status_code == 200

    created_ct = created_ct.data
    assert created_ct["topic"]["id"] == pt_id


def test_get_topic_not_found(client_admin):
    result = client_admin.get("/api/v1/topics/%s" % uuid.uuid4())
    assert result.status_code == 404


def test_delete_topic_by_id(client_admin, rhel_80_topic_id):
    result = client_admin.get("/api/v1/topics/%s" % rhel_80_topic_id)
    topic_etag = result.data["topic"]["etag"]
    topic = topic_removal(client_admin, rhel_80_topic_id, topic_etag)
    assert topic.status_code == 204

    gct = client_admin.get("/api/v1/topics/%s" % rhel_80_topic_id)
    assert gct.status_code == 404


def test_delete_topic_by_id_as_user(client_admin, client_user1, rhel_product):
    data = {
        "name": "tname",
        "product_id": rhel_product["id"],
        "component_types": ["type1", "type2"],
    }
    pt = client_admin.post("/api/v1/topics", data=data)
    pt_id = pt.data["topic"]["id"]
    assert pt.status_code == 201

    created_ct = client_admin.get("/api/v1/topics/%s" % pt_id)
    assert created_ct.status_code == 200

    deleted_ct = client_user1.delete(
        "/api/v1/topics/%s" % pt_id, headers={"If-match": pt.data["topic"]["etag"]}
    )
    assert deleted_ct.status_code == 401


def test_delete_topic_archive_dependencies(client_admin, rhel_product):
    topic = client_admin.post(
        "/api/v1/topics",
        data={
            "name": "topic_name",
            "product_id": rhel_product["id"],
            "component_types": ["type1", "type2"],
        },
    )
    topic_id = topic.data["topic"]["id"]
    assert topic.status_code == 201

    data = {
        "name": "pname",
        "type": "gerrit_review",
        "url": "http://example.com/",
        "topic_id": topic_id,
        "state": "active",
    }
    component = client_admin.post("/api/v1/components", data=data)
    component_id = component.data["component"]["id"]
    assert component.status_code == 201

    url = "/api/v1/topics/%s" % topic_id
    deleted_topic = client_admin.delete(
        url, headers={"If-match": topic.data["topic"]["etag"]}
    )
    assert deleted_topic.status_code == 204

    deleted_component = client_admin.get("/api/v1/component/%s" % component_id)
    assert deleted_component.status_code == 404


def test_purge_topic(client_admin, rhel_product):
    data = {
        "name": "tname",
        "product_id": rhel_product["id"],
        "component_types": ["type1", "type2"],
    }
    pt = client_admin.post("/api/v1/topics", data=data)
    pt_id = pt.data["topic"]["id"]
    assert pt.status_code == 201

    ppt = client_admin.delete(
        "/api/v1/topics/%s" % pt_id, headers={"If-match": pt.data["topic"]["etag"]}
    )
    assert ppt.status_code == 204


def test_get_all_topics_sorted(client_admin, rhel_product):
    t1 = {"name": "c", "product_id": rhel_product["id"], "component_types": ["ct1"]}
    tid_1 = client_admin.post("/api/v1/topics", data=t1).data["topic"]["id"]
    t2 = {"name": "b", "product_id": rhel_product["id"], "component_types": ["ct1"]}
    tid_2 = client_admin.post("/api/v1/topics", data=t2).data["topic"]["id"]
    t3 = {"name": "a", "product_id": rhel_product["id"], "component_types": ["ct1"]}
    tid_3 = client_admin.post("/api/v1/topics", data=t3).data["topic"]["id"]

    def get_ids(path):
        return [i["id"] for i in client_admin.get(path).data["topics"]]

    assert get_ids("/api/v1/topics") == [tid_3, tid_2, tid_1]
    assert get_ids("/api/v1/topics?sort=created_at") == [tid_1, tid_2, tid_3]
    assert get_ids("/api/v1/topics?sort=-created_at") == [tid_3, tid_2, tid_1]
    assert get_ids("/api/v1/topics?sort=name") == [tid_3, tid_2, tid_1]


def test_delete_topic_not_found(client_admin):
    result = client_admin.delete(
        "/api/v1/topics/%s" % uuid.uuid4(), headers={"If-match": uuid.uuid4()}
    )
    assert result.status_code == 404


def test_put_topics(client_admin, rhel_80_topic_id, rhel_product):
    pt = client_admin.post(
        "/api/v1/topics",
        data={
            "name": "pname",
            "product_id": rhel_product["id"],
            "component_types": ["type1", "type2"],
        },
    )
    assert pt.status_code == 201

    pt_etag = pt.headers.get("ETag")

    gt = client_admin.get("/api/v1/topics/%s" % pt.data["topic"]["id"])
    assert gt.status_code == 200

    ppt = client_admin.put(
        "/api/v1/topics/%s" % pt.data["topic"]["id"],
        data={"name": "nname", "next_topic_id": rhel_80_topic_id},
        headers={"If-match": pt_etag},
    )
    assert ppt.status_code == 200

    gt = client_admin.get("/api/v1/topics/%s?embed=next_topic" % pt.data["topic"]["id"])
    assert gt.status_code == 200
    assert gt.data["topic"]["name"] == "nname"
    assert gt.data["topic"]["next_topic"]["name"] == "RHEL-8.0"
    assert gt.data["topic"]["next_topic"]["id"] == rhel_80_topic_id


def test_remove_next_topic_from_topic(client_admin, rhel_80_topic_id, rhel_product):
    request = client_admin.post(
        "/api/v1/topics",
        data={
            "name": "topic 1",
            "next_topic_id": rhel_80_topic_id,
            "product_id": rhel_product["id"],
        },
    )
    assert request.status_code == 201
    new_topic_id = request.data["topic"]["id"]

    t = client_admin.get("/api/v1/topics/%s" % new_topic_id).data["topic"]
    assert t["next_topic_id"] == rhel_80_topic_id

    request2 = client_admin.put(
        "/api/v1/topics/%s" % new_topic_id,
        data={"next_topic_id": None},
        headers={"If-match": request.headers.get("ETag")},
    )
    assert request2.status_code == 200

    t = client_admin.get("/api/v1/topics/%s" % new_topic_id).data["topic"]
    assert t["next_topic_id"] is None

    request3 = client_admin.put(
        "/api/v1/topics/%s" % new_topic_id,
        data={"next_topic_id": rhel_80_topic_id},
        headers={"If-match": request2.headers.get("ETag")},
    )
    assert request3.status_code == 200

    t = client_admin.get("/api/v1/topics/%s" % new_topic_id).data["topic"]
    assert t["next_topic_id"] == rhel_80_topic_id


def test_component_success_update_field_by_field(client_admin, rhel_80_topic_id):
    t = client_admin.get("/api/v1/topics/%s" % rhel_80_topic_id).data["topic"]

    client_admin.put(
        "/api/v1/topics/%s" % rhel_80_topic_id,
        data={"state": "inactive"},
        headers={"If-match": t["etag"]},
    )

    t = client_admin.get("/api/v1/topics/%s" % rhel_80_topic_id).data["topic"]

    assert t["name"] == "RHEL-8.0"
    assert t["state"] == "inactive"

    client_admin.put(
        "/api/v1/topics/%s" % rhel_80_topic_id,
        data={"name": "topic_name2"},
        headers={"If-match": t["etag"]},
    )

    t = client_admin.get("/api/v1/topics/%s" % t["id"]).data["topic"]

    assert t["name"] == "topic_name2"
    assert t["state"] == "inactive"


def test_success_get_topics_embed(client_admin, rhel_80_topic_id, rhel_product):
    result = client_admin.get("/api/v1/topics/%s/?embed=product" % rhel_80_topic_id)

    assert result.status_code == 200
    assert "product" in result.data["topic"].keys()

    client_admin.post(
        "/api/v1/topics",
        data={"name": "topic_without_product", "product_id": rhel_product["id"]},
    )

    result = client_admin.get("/api/v1/topics")
    assert result.data["topics"][0]["product"]["id"]


def test_get_topic_by_id_export_control_true(
    client_admin, client_user1, team1_id, rhel_product, rhel_80_topic
):
    request = client_admin.post(
        "/api/v1/products/%s/teams" % rhel_product["id"], data={"team_id": team1_id}
    )
    assert request.status_code == 201
    request = client_user1.get("/api/v1/topics/%s" % rhel_80_topic["id"])
    assert request.status_code == 200
    assert request.data["topic"]["id"] == rhel_80_topic["id"]


def test_get_topic_by_id_export_control_false(
    client_admin, client_user1, team1_id, rhel_product, rhel_81_topic
):
    request = client_admin.post(
        "/api/v1/products/%s/teams" % rhel_product["id"], data={"team_id": team1_id}
    )
    assert request.status_code == 201
    assert rhel_81_topic["export_control"] is False
    assert (
        client_user1.get("/api/v1/topics/%s" % rhel_81_topic["id"]).status_code == 401
    )

    team_user = client_admin.get("/api/v1/teams/%s" % team1_id).data["team"]
    assert (
        client_admin.put(
            "/api/v1/teams/%s" % team_user["id"],
            data={"has_pre_release_access": True},
            headers={"If-match": team_user["etag"]},
        ).status_code
        == 200
    )
    request = client_user1.get("/api/v1/topics/%s" % rhel_81_topic["id"])
    assert request.status_code == 200
    assert request.data["topic"]["id"] == rhel_81_topic["id"]


def test_get_topic_with_rolling_topic_name(client_admin, rhel_product):
    r1 = client_admin.post(
        "/api/v1/topics",
        data={
            "name": "RHEL-8.4",
            "product_id": rhel_product["id"],
            "component_types": ["compose"],
        },
    )
    assert r1.status_code == 201
    RHEL_84 = r1.data["topic"]
    r2 = client_admin.post(
        "/api/v1/topics",
        data={
            "name": "RHEL-8.5",
            "product_id": rhel_product["id"],
            "component_types": ["compose"],
        },
    )
    assert r2.status_code == 201
    RHEL_85 = r2.data["topic"]
    assert client_admin.get("/api/v1/topics").data["_meta"]["count"] == 2

    latest_rhel_85 = client_admin.get(
        "/api/v1/topics?where=name:RHEL-8*&limit=1&offset=0"
    )
    assert latest_rhel_85.status_code == 200
    assert latest_rhel_85.data["_meta"]["count"] == 2
    assert latest_rhel_85.data["topics"][0]["id"] == RHEL_85["id"]

    latest_rhel_8 = client_admin.get("/api/v1/topics?where=name:RHEL-8*")
    assert latest_rhel_8.status_code == 200
    assert latest_rhel_8.data["_meta"]["count"] == 2
    assert latest_rhel_8.data["topics"][0]["id"] == RHEL_85["id"]
    assert latest_rhel_8.data["topics"][1]["id"] == RHEL_84["id"]

    latest_rhel_7 = client_admin.get("/api/v1/topics?where=name:RHEL-7*")
    assert latest_rhel_7.status_code == 200
    assert latest_rhel_7.data["_meta"]["count"] == 0


def test_notifications(client_admin, client_user1, user1_id, rhel_80_topic_id):
    r = client_admin.get("/api/v1/topics/%s/notifications/users" % rhel_80_topic_id)
    assert len(r.data["users"]) == 0

    r = client_user1.get("/api/v1/topics/notifications")
    assert len(r.data["topics"]) == 0

    r = client_user1.post("/api/v1/topics/%s/notifications" % rhel_80_topic_id)
    assert r.status_code == 201

    r = client_admin.get("/api/v1/topics/%s/notifications/users" % rhel_80_topic_id)
    assert r.data["users"][0]["id"] == user1_id

    r = client_user1.get("/api/v1/topics/notifications")
    assert len(r.data["topics"]) == 1
    assert r.data["topics"][0]["id"] == rhel_80_topic_id

    r = client_user1.delete("/api/v1/topics/%s/notifications" % rhel_80_topic_id)
    assert r.status_code == 204

    r = client_admin.get("/api/v1/topics/%s/notifications/users" % rhel_80_topic_id)
    assert len(r.data["users"]) == 0

    r = client_user1.get("/api/v1/topics/notifications")
    assert len(r.data["topics"]) == 0
