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


def test_create_topics(admin, product):
    topic = topic_creation(admin, product).data
    assert topic["topic"]["name"] == "tname"
    assert topic["topic"]["component_types"] == ["type1", "type2"]


def test_topic_creation_with_opts(admin, product):
    data = {
        "name": "tname",
        "product_id": product["id"],
        "component_types": ["type1", "type2"],
        "component_types_optional": ["type3"],
        "data": {"foo": "bar"},
    }
    pt = admin.post("/api/v1/topics", data=data).data
    pt_id = pt["topic"]["id"]
    t = admin.get("/api/v1/topics/%s" % pt_id).data
    assert t["topic"]["data"]["foo"] == "bar"
    assert t["topic"]["component_types_optional"] == ["type3"]


def test_create_topic_as_feeder(feeder_context, product):
    topic = topic_creation(feeder_context, product).data
    assert topic["topic"]["name"] == "tname"
    assert topic["topic"]["component_types"] == ["type1", "type2"]


def test_create_topics_as_user(user, product):
    data = {
        "name": "tname",
        "product_id": product["id"],
        "component_types": ["type1", "type2"],
    }
    status_code = user.post("/api/v1/topics", data=data).status_code
    assert status_code == 401


def test_create_topic_lowercase_component_types(admin, product):
    data = {
        "name": "tname",
        "product_id": product["id"],
        "component_types": ["tYpe1", "Type2"],
    }
    topic = admin.post("/api/v1/topics", data=data).data["topic"]
    topic = admin.get("/api/v1/topics/%s" % topic["id"]).data["topic"]
    assert topic["component_types"] == ["type1", "type2"]


def test_update_topics_as_admin(admin, topic_id):
    topic = topic_update(admin, topic_id).data["topic"]
    assert topic["component_types"] == ["lol1", "lol2"]
    assert topic["data"]["foo"] == "bar"


def test_update_topic_as_feeder(feeder_context, topic_id):
    topic = topic_update(feeder_context, topic_id).data["topic"]
    assert topic["component_types"] == ["lol1", "lol2"]
    assert topic["data"]["foo"] == "bar"


def test_update_topic_lowercase_component_types(admin, product):
    data = {
        "name": "tname",
        "product_id": product["id"],
    }
    topic = admin.post("/api/v1/topics", data=data).data["topic"]
    topic = admin.put(
        "/api/v1/topics/%s" % topic["id"],
        data={"component_types": ["tYpe1", "Type2"]},
        headers={"If-match": topic["etag"]},
    ).data["topic"]
    topic = admin.get("/api/v1/topics/%s" % topic["id"]).data["topic"]
    assert topic["component_types"] == ["type1", "type2"]


def test_change_topic_state(admin, topic_id):
    t = admin.get("/api/v1/topics/" + topic_id).data["topic"]
    data = {"state": "inactive"}
    r = admin.put(
        "/api/v1/topics/" + topic_id, data=data, headers={"If-match": t["etag"]}
    )
    assert r.status_code == 200
    assert r.data["topic"]["state"] == "inactive"


def test_change_topic_to_invalid_state(admin, topic_id):
    t = admin.get("/api/v1/topics/" + topic_id).data["topic"]
    data = {"state": "kikoolol"}
    r = admin.put(
        "/api/v1/topics/" + topic_id, data=data, headers={"If-match": t["etag"]}
    )
    assert r.status_code == 400
    current_topic = admin.get("/api/v1/topics/" + topic_id)
    assert current_topic.status_code == 200
    assert current_topic.data["topic"]["state"] == "active"


def test_create_topics_already_exist(admin, product):
    data = {
        "name": "tname",
        "product_id": product["id"],
        "component_types": ["type1", "type2"],
    }
    pstatus_code = admin.post("/api/v1/topics", data=data).status_code
    assert pstatus_code == 201

    data = {
        "name": "tname",
        "product_id": product["id"],
        "component_types": ["type1", "type2"],
    }
    pstatus_code = admin.post("/api/v1/topics", data=data).status_code
    assert pstatus_code == 409


def test_get_all_topics_by_admin(admin, product):
    created_topics_ids = []
    for i in range(5):
        pc = admin.post(
            "/api/v1/topics",
            data={
                "name": "tname%s" % uuid.uuid4(),
                "product_id": product["id"],
                "component_types": ["type1", "type2"],
            },
        ).data
        created_topics_ids.append(pc["topic"]["id"])
    created_topics_ids.sort()

    db_all_cs = admin.get("/api/v1/topics").data
    db_all_cs = db_all_cs["topics"]
    db_all_cs_ids = [db_ct["id"] for db_ct in db_all_cs]
    db_all_cs_ids.sort()

    assert db_all_cs_ids == created_topics_ids


def test_get_all_topics_by_user_and_remoteci(
    admin, user, remoteci_context, team_user_id, product
):
    pat = admin.post(
        "/api/v1/products/%s/teams" % product["id"], data={"team_id": team_user_id}
    )
    assert pat.status_code == 201

    def test(caller, topic_name):
        # create a topic with export_control==False
        my_topic = admin.post(
            "/api/v1/topics",
            data={
                "name": topic_name,
                "product_id": product["id"],
                "export_control": False,
                "component_types": ["type1", "type2"],
            },
        )
        assert my_topic.status_code == 201
        my_topic_id = my_topic.data["topic"]["id"]
        my_topic_etag = my_topic.data["topic"]["etag"]

        team_user = admin.get("/api/v1/teams/%s" % team_user_id).data["team"]
        assert team_user["has_pre_release_access"] is False

        # user should not find it
        my_topic = caller.get("/api/v1/topics?where=name:%s" % topic_name)
        assert len(my_topic.data["topics"]) == 0

        # allow team to access pre release content
        assert (
            admin.put(
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
        team_user = admin.get("/api/v1/teams/%s" % team_user_id).data["team"]
        assert (
            admin.put(
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
        admin.put(
            "/api/v1/topics/%s" % my_topic_id,
            headers={"If-match": my_topic_etag},
            data={"export_control": True},
        )

        # user should see the topic now
        my_topic = caller.get("/api/v1/topics?where=name:%s" % topic_name)
        assert my_topic.data["topics"][0]["name"] == topic_name

    test(user, "my_new_topic_1")
    test(remoteci_context, "my_new_topic_2")


def test_get_all_topics_with_pagination(admin, product):
    cs = admin.get("/api/v1/topics").data
    nb_topics_init = cs["_meta"]["count"]

    # create 20 topic types and check meta data count
    for i in range(20):
        admin.post(
            "/api/v1/topics",
            data={
                "name": "tname%s" % uuid.uuid4(),
                "product_id": product["id"],
                "component_types": ["type1", "type2"],
            },
        )
    cs = admin.get("/api/v1/topics").data
    assert cs["_meta"]["count"] == nb_topics_init + 20

    # verify limit and offset are working well
    for i in range(4):
        cs = admin.get("/api/v1/topics?limit=5&offset=%s" % (i * 5)).data
        assert len(cs["topics"]) == 5

    # if offset is out of bound, the api returns an empty list
    cs = admin.get("/api/v1/topics?limit=5&offset=300")
    assert cs.status_code == 200
    assert cs.data["topics"] == []


def test_get_all_topics_with_where(admin, product):
    # create 20 topic types and check meta data count
    topics = {}
    for i in range(20):
        t_name = str(uuid.uuid4())
        r = admin.post(
            "/api/v1/topics",
            data={
                "name": t_name,
                "product_id": product["id"],
                "component_types": ["type1", "type2"],
            },
        ).data
        topics[t_name] = r["topic"]["id"]

    for t_name, t_id in topics.items():
        r = admin.get("/api/v1/topics?where=name:%s&limit=1&offset=0" % t_name).data
        assert r["_meta"]["count"] == 1
        assert r["topics"][0]["id"] == t_id


def test_get_topic_by_id(admin, user, rhel_product):
    data = {
        "name": "tname",
        "product_id": rhel_product["id"],
        "component_types": ["type1", "type2"],
        "export_control": True,
    }
    pt = admin.post("/api/v1/topics", data=data).data
    pt_id = pt["topic"]["id"]

    # get by uuid
    created_ct = user.get("/api/v1/topics/%s" % pt_id)
    assert created_ct.status_code == 200

    created_ct = created_ct.data
    assert created_ct["topic"]["id"] == pt_id


def test_get_topic_not_found(admin):
    result = admin.get("/api/v1/topics/%s" % uuid.uuid4())
    assert result.status_code == 404


def test_delete_topic_by_id(admin, topic_id):
    result = admin.get("/api/v1/topics/%s" % topic_id)
    topic_etag = result.data["topic"]["etag"]
    topic = topic_removal(admin, topic_id, topic_etag)
    assert topic.status_code == 204

    gct = admin.get("/api/v1/topics/%s" % topic_id)
    assert gct.status_code == 404


def test_delete_topic_by_id_as_user(admin, user, product):
    data = {
        "name": "tname",
        "product_id": product["id"],
        "component_types": ["type1", "type2"],
    }
    pt = admin.post("/api/v1/topics", data=data)
    pt_id = pt.data["topic"]["id"]
    assert pt.status_code == 201

    created_ct = admin.get("/api/v1/topics/%s" % pt_id)
    assert created_ct.status_code == 200

    deleted_ct = user.delete(
        "/api/v1/topics/%s" % pt_id, headers={"If-match": pt.data["topic"]["etag"]}
    )
    assert deleted_ct.status_code == 401


def test_delete_topic_archive_dependencies(admin, product):
    topic = admin.post(
        "/api/v1/topics",
        data={
            "name": "topic_name",
            "product_id": product["id"],
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
    component = admin.post("/api/v1/components", data=data)
    component_id = component.data["component"]["id"]
    assert component.status_code == 201

    url = "/api/v1/topics/%s" % topic_id
    deleted_topic = admin.delete(url, headers={"If-match": topic.data["topic"]["etag"]})
    assert deleted_topic.status_code == 204

    deleted_component = admin.get("/api/v1/component/%s" % component_id)
    assert deleted_component.status_code == 404


def test_purge_topic(admin, product):
    data = {
        "name": "tname",
        "product_id": product["id"],
        "component_types": ["type1", "type2"],
    }
    pt = admin.post("/api/v1/topics", data=data)
    pt_id = pt.data["topic"]["id"]
    assert pt.status_code == 201

    ppt = admin.delete(
        "/api/v1/topics/%s" % pt_id, headers={"If-match": pt.data["topic"]["etag"]}
    )
    assert ppt.status_code == 204


def test_get_all_topics_sorted(admin, product):
    t1 = {"name": "c", "product_id": product["id"], "component_types": ["ct1"]}
    tid_1 = admin.post("/api/v1/topics", data=t1).data["topic"]["id"]
    t2 = {"name": "b", "product_id": product["id"], "component_types": ["ct1"]}
    tid_2 = admin.post("/api/v1/topics", data=t2).data["topic"]["id"]
    t3 = {"name": "a", "product_id": product["id"], "component_types": ["ct1"]}
    tid_3 = admin.post("/api/v1/topics", data=t3).data["topic"]["id"]

    def get_ids(path):
        return [i["id"] for i in admin.get(path).data["topics"]]

    assert get_ids("/api/v1/topics") == [tid_3, tid_2, tid_1]
    assert get_ids("/api/v1/topics?sort=created_at") == [tid_1, tid_2, tid_3]
    assert get_ids("/api/v1/topics?sort=-created_at") == [tid_3, tid_2, tid_1]
    assert get_ids("/api/v1/topics?sort=name") == [tid_3, tid_2, tid_1]


def test_delete_topic_not_found(admin):
    result = admin.delete(
        "/api/v1/topics/%s" % uuid.uuid4(), headers={"If-match": uuid.uuid4()}
    )
    assert result.status_code == 404


def test_put_topics(admin, topic_id, product):
    pt = admin.post(
        "/api/v1/topics",
        data={
            "name": "pname",
            "product_id": product["id"],
            "component_types": ["type1", "type2"],
        },
    )
    assert pt.status_code == 201

    pt_etag = pt.headers.get("ETag")

    gt = admin.get("/api/v1/topics/%s" % pt.data["topic"]["id"])
    assert gt.status_code == 200

    ppt = admin.put(
        "/api/v1/topics/%s" % pt.data["topic"]["id"],
        data={"name": "nname", "next_topic_id": topic_id},
        headers={"If-match": pt_etag},
    )
    assert ppt.status_code == 200

    gt = admin.get("/api/v1/topics/%s?embed=next_topic" % pt.data["topic"]["id"])
    assert gt.status_code == 200
    assert gt.data["topic"]["name"] == "nname"
    assert gt.data["topic"]["next_topic"]["name"] == "RHEL-8.0"
    assert gt.data["topic"]["next_topic"]["id"] == topic_id


def test_remove_next_topic_from_topic(admin, topic_id, product):
    request = admin.post(
        "/api/v1/topics",
        data={
            "name": "topic 1",
            "next_topic_id": topic_id,
            "product_id": product["id"],
        },
    )
    assert request.status_code == 201
    new_topic_id = request.data["topic"]["id"]

    t = admin.get("/api/v1/topics/%s" % new_topic_id).data["topic"]
    assert t["next_topic_id"] == topic_id

    request2 = admin.put(
        "/api/v1/topics/%s" % new_topic_id,
        data={"next_topic_id": None},
        headers={"If-match": request.headers.get("ETag")},
    )
    assert request2.status_code == 200

    t = admin.get("/api/v1/topics/%s" % new_topic_id).data["topic"]
    assert t["next_topic_id"] is None

    request3 = admin.put(
        "/api/v1/topics/%s" % new_topic_id,
        data={"next_topic_id": topic_id},
        headers={"If-match": request2.headers.get("ETag")},
    )
    assert request3.status_code == 200

    t = admin.get("/api/v1/topics/%s" % new_topic_id).data["topic"]
    assert t["next_topic_id"] == topic_id


def test_component_success_update_field_by_field(admin, topic_id):
    t = admin.get("/api/v1/topics/%s" % topic_id).data["topic"]

    admin.put(
        "/api/v1/topics/%s" % topic_id,
        data={"state": "inactive"},
        headers={"If-match": t["etag"]},
    )

    t = admin.get("/api/v1/topics/%s" % topic_id).data["topic"]

    assert t["name"] == "RHEL-8.0"
    assert t["state"] == "inactive"

    admin.put(
        "/api/v1/topics/%s" % topic_id,
        data={"name": "topic_name2"},
        headers={"If-match": t["etag"]},
    )

    t = admin.get("/api/v1/topics/%s" % t["id"]).data["topic"]

    assert t["name"] == "topic_name2"
    assert t["state"] == "inactive"


def test_success_get_topics_embed(admin, topic_id, product):
    result = admin.get("/api/v1/topics/%s/?embed=product" % topic_id)

    assert result.status_code == 200
    assert "product" in result.data["topic"].keys()

    admin.post(
        "/api/v1/topics",
        data={"name": "topic_without_product", "product_id": product["id"]},
    )

    result = admin.get("/api/v1/topics")
    assert result.data["topics"][0]["product"]["id"]


def test_get_topic_by_id_export_control_true(
    admin, user, team_user_id, rhel_product, rhel_80_topic
):
    request = admin.post(
        "/api/v1/products/%s/teams" % rhel_product["id"], data={"team_id": team_user_id}
    )
    assert request.status_code == 201
    request = user.get("/api/v1/topics/%s" % rhel_80_topic["id"])
    assert request.status_code == 200
    assert request.data["topic"]["id"] == rhel_80_topic["id"]


def test_get_topic_by_id_export_control_false(
    admin, user, team_user_id, rhel_product, rhel_81_topic
):
    request = admin.post(
        "/api/v1/products/%s/teams" % rhel_product["id"], data={"team_id": team_user_id}
    )
    assert request.status_code == 201
    assert rhel_81_topic["export_control"] is False
    assert user.get("/api/v1/topics/%s" % rhel_81_topic["id"]).status_code == 401

    team_user = admin.get("/api/v1/teams/%s" % team_user_id).data["team"]
    assert (
        admin.put(
            "/api/v1/teams/%s" % team_user["id"],
            data={"has_pre_release_access": True},
            headers={"If-match": team_user["etag"]},
        ).status_code
        == 200
    )
    request = user.get("/api/v1/topics/%s" % rhel_81_topic["id"])
    assert request.status_code == 200
    assert request.data["topic"]["id"] == rhel_81_topic["id"]


def test_get_topic_with_rolling_topic_name(admin, product):
    r1 = admin.post(
        "/api/v1/topics",
        data={
            "name": "RHEL-8.4",
            "product_id": product["id"],
            "component_types": ["compose"],
        },
    )
    assert r1.status_code == 201
    RHEL_84 = r1.data["topic"]
    r2 = admin.post(
        "/api/v1/topics",
        data={
            "name": "RHEL-8.5",
            "product_id": product["id"],
            "component_types": ["compose"],
        },
    )
    assert r2.status_code == 201
    RHEL_85 = r2.data["topic"]
    assert admin.get("/api/v1/topics").data["_meta"]["count"] == 2

    latest_rhel_85 = admin.get("/api/v1/topics?where=name:RHEL-8*&limit=1&offset=0")
    assert latest_rhel_85.status_code == 200
    assert latest_rhel_85.data["_meta"]["count"] == 2
    assert latest_rhel_85.data["topics"][0]["id"] == RHEL_85["id"]

    latest_rhel_8 = admin.get("/api/v1/topics?where=name:RHEL-8*")
    assert latest_rhel_8.status_code == 200
    assert latest_rhel_8.data["_meta"]["count"] == 2
    assert latest_rhel_8.data["topics"][0]["id"] == RHEL_85["id"]
    assert latest_rhel_8.data["topics"][1]["id"] == RHEL_84["id"]

    latest_rhel_7 = admin.get("/api/v1/topics?where=name:RHEL-7*")
    assert latest_rhel_7.status_code == 200
    assert latest_rhel_7.data["_meta"]["count"] == 0


def test_notifications(admin, user, user_id, topic_user_id):
    r = admin.get("/api/v1/topics/%s/notifications/users" % topic_user_id)
    assert len(r.data["users"]) == 0

    r = user.get("/api/v1/topics/notifications")
    assert len(r.data["topics"]) == 0

    r = user.post("/api/v1/topics/%s/notifications" % topic_user_id)
    assert r.status_code == 201

    r = admin.get("/api/v1/topics/%s/notifications/users" % topic_user_id)
    assert r.data["users"][0]["id"] == user_id

    r = user.get("/api/v1/topics/notifications")
    assert len(r.data["topics"]) == 1
    assert r.data["topics"][0]["id"] == topic_user_id

    r = user.delete("/api/v1/topics/%s/notifications" % topic_user_id)
    assert r.status_code == 204

    r = admin.get("/api/v1/topics/%s/notifications/users" % topic_user_id)
    assert len(r.data["users"]) == 0

    r = user.get("/api/v1/topics/notifications")
    assert len(r.data["topics"]) == 0
