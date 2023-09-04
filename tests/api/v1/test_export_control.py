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

import mock
import six

from dci.common import utils
from dci.stores.s3 import S3

AWSS3 = "dci.stores.s3.S3"


def test_topics_export_control_true(user, epm, rhel_81_topic):
    assert (
        user.get("/api/v1/topics/%s/components" % rhel_81_topic["id"]).status_code
        == 401
    )

    topic = epm.get("/api/v1/topics/%s" % rhel_81_topic["id"]).data["topic"]
    assert topic["export_control"] is False

    epm.put(
        "/api/v1/topics/%s" % rhel_81_topic["id"],
        data={"export_control": True},
        headers={"If-match": rhel_81_topic["etag"]},
    )

    topic = epm.get("/api/v1/topics/%s" % rhel_81_topic["id"]).data["topic"]
    assert topic["export_control"]
    # team_user_id is associated to the product and the topic is exported
    # then it should have access to the topic's components
    assert (
        user.get("/api/v1/topics/%s/components" % rhel_81_topic["id"]).status_code
        == 200
    )


def test_topics_export_control_false(user, epm, rhel_80_topic):
    assert (
        user.get("/api/v1/topics/%s/components" % rhel_80_topic["id"]).status_code
        == 200
    )

    topic = epm.get("/api/v1/topics/%s" % rhel_80_topic["id"]).data["topic"]
    assert topic["export_control"]

    epm.put(
        "/api/v1/topics/%s" % rhel_80_topic["id"],
        data={"export_control": False},
        headers={"If-match": rhel_80_topic["etag"]},
    )

    topic = epm.get("/api/v1/topics/%s" % rhel_80_topic["id"]).data["topic"]
    assert topic["export_control"] is False
    # team_user_id is associated to the product and the topic is not exported anymore
    # then user should lose the access to the topic's components
    assert (
        user.get("/api/v1/topics/%s/components" % rhel_80_topic["id"]).status_code
        == 401
    )


def test_components_export_control_true(user, epm, rhel_80_topic, rhel_80_component):
    topic = epm.get("/api/v1/topics/%s" % rhel_80_topic["id"]).data["topic"]
    assert topic["export_control"] is True

    with mock.patch(AWSS3, spec=S3) as mock_s3:
        mockito = mock.MagicMock()
        mockito.get.return_value = ["test", six.StringIO("lollollel")]
        head_result = {
            "etag": utils.gen_etag(),
            "content-type": "stream",
            "content-length": 1,
        }
        mockito.head.return_value = head_result
        mock_s3.return_value = mockito

        url = "/api/v1/components/%s/files" % rhel_80_component["id"]
        c_file = epm.post(url, data="lol")
        c_file_1_id = c_file.data["component_file"]["id"]
        # team_user_id is not subscribing to topic_user_id but it's
        # associated to the product thus it can access the topic's components
        assert (
            user.get("/api/v1/components/%s" % rhel_80_component["id"]).status_code
            == 200
        )
        assert (
            user.get(
                "/api/v1/components/%s/files" % rhel_80_component["id"]
            ).status_code
            == 200
        )
        assert (
            user.get(
                "/api/v1/components/%s/files/%s"
                % (rhel_80_component["id"], c_file_1_id)
            ).status_code
            == 200
        )
        assert (
            user.get(
                "/api/v1/components/%s/files/%s/content"
                % (rhel_80_component["id"], c_file_1_id)
            ).status_code
            == 200
        )


def test_components_export_control_false(
    user, epm, rhel_81_component, team_user_id, rhel_81_topic
):
    with mock.patch(AWSS3, spec=S3) as mock_s3:
        mockito = mock.MagicMock()
        mockito.get.return_value = ["test", six.StringIO("lollollel")]
        head_result = {
            "etag": utils.gen_etag(),
            "content-type": "stream",
            "content-length": 1,
        }
        mockito.head.return_value = head_result
        mock_s3.return_value = mockito

        url = "/api/v1/components/%s/files" % rhel_81_component["id"]
        c_file = epm.post(url, data="lol")
        c_file_1_id = c_file.data["component_file"]["id"]

        # team_user_id is associated to the product but not to the topic,
        # since the topic is not exported the user doesn't have the access
        assert (
            user.get("/api/v1/components/%s" % rhel_81_component["id"]).status_code
            == 401
        )
        assert (
            user.get(
                "/api/v1/components/%s/files" % rhel_81_component["id"]
            ).status_code
            == 401
        )
        assert (
            user.get(
                "/api/v1/components/%s/files/%s"
                % (rhel_81_component["id"], c_file_1_id)
            ).status_code
            == 401
        )
        assert (
            user.get(
                "/api/v1/components/%s/files/%s/content"
                % (rhel_81_component["id"], c_file_1_id)
            ).status_code
            == 401
        )

        # explicitly allow team to download rhel_81_component
        epm.post(
            "/api/v1/topics/%s/teams" % rhel_81_topic["id"],
            data={"team_id": team_user_id},
        )

        # team_user_id is now associated with the topic
        assert (
            user.get("/api/v1/components/%s" % rhel_81_component["id"]).status_code
            == 200
        )
        assert (
            user.get(
                "/api/v1/components/%s/files" % rhel_81_component["id"]
            ).status_code
            == 200
        )
        assert (
            user.get(
                "/api/v1/components/%s/files/%s"
                % (rhel_81_component["id"], c_file_1_id)
            ).status_code
            == 200
        )
        assert (
            user.get(
                "/api/v1/components/%s/files/%s/content"
                % (rhel_81_component["id"], c_file_1_id)
            ).status_code
            == 200
        )
