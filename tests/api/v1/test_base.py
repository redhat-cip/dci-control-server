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


def test_purge_resource(admin, product):
    data = {
        "name": "tname",
        "product_id": product["id"],
        "component_types": ["type1", "type2"],
    }
    pt = admin.post("/api/v1/topics", data=data)
    pt_id = pt.data["topic"]["id"]
    assert pt.status_code == 201

    ppt = admin.delete("/api/v1/topics/%s" % pt_id)
    assert ppt.status_code == 204

    to_purge = admin.get("/api/v1/topics/purge").data
    assert len(to_purge["topics"]) == 1

    to_purge = admin.post("/api/v1/topics/purge")
    assert to_purge.status_code == 204

    to_purge = admin.get("/api/v1/topics/purge").data
    assert len(to_purge["topics"]) == 0
