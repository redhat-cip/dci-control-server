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


def allow_team_to_access_product(client, team_id, product_id):
    assert (
        client.post(
            "/api/v1/products/%s/teams" % product_id,
            data={"team_id": team_id},
        ).status_code
        == 201
    )


def deny_team_to_access_product(client, team_id, product_id):
    assert (
        client.delete(
            "/api/v1/products/%s/teams/%s" % (product_id, team_id)
        ).status_code
        == 204
    )


def change_team_pre_release_access(client, team, has_access=True):
    res = client.put(
        "/api/v1/teams/%s" % team["id"],
        data={"has_pre_release_access": has_access},
        headers={"If-match": team["etag"]},
    )
    assert res.status_code == 200
    return res.data["team"]


def test_user_can_access_ga_topic_s_components_if_has_access_to_the_product(
    epm, user, team_user, rhel_product, rhel_80_topic
):
    assert rhel_80_topic["export_control"]

    # user can list the components because he has access to the RHEL product
    assert (
        user.get("/api/v1/topics/%s/components" % rhel_80_topic["id"]).status_code
        == 200
    )

    # epm remove the RHEL product permission
    deny_team_to_access_product(epm, team_user["id"], rhel_product["id"])

    # topic export_control is true but the user can't access the components
    # because his team doesn't have access to the product now
    assert (
        user.get("/api/v1/topics/%s/components" % rhel_80_topic["id"]).status_code
        == 401
    )


def test_user_can_access_pre_ga_topic_s_components_if_team_has_pre_release_access(
    epm, user, team_user, rhel_product, rhel_81_topic
):
    assert rhel_81_topic["export_control"] is False

    # the user can't access the components because his team doesn't have access to the product
    assert (
        user.get("/api/v1/topics/%s/components" % rhel_81_topic["id"]).status_code
        == 401
    )

    # give access to the product
    assert rhel_product["id"] == rhel_81_topic["product_id"]
    allow_team_to_access_product(epm, team_user["id"], rhel_product["id"])

    # the user still doesn't have access to the component
    # because his team doesn't have the has_pre_release_access and topic is not exported
    assert (
        user.get("/api/v1/topics/%s/components" % rhel_81_topic["id"]).status_code
        == 401
    )

    # change has_pre_release_access for the team
    change_team_pre_release_access(epm, team_user, has_access=True)

    # now the user can access the components
    assert (
        user.get("/api/v1/topics/%s/components" % rhel_81_topic["id"]).status_code
        == 200
    )


def test_user_cant_access_topic_components_with_has_pre_release_access_if_no_product_access(
    epm, user, team_user, rhel_product, rhel_81_topic
):
    assert rhel_81_topic["export_control"] is False

    # the user can't access the components because has_pre_release_access not set
    assert (
        user.get("/api/v1/topics/%s/components" % rhel_81_topic["id"]).status_code
        == 401
    )

    # allow pre release access for the team
    change_team_pre_release_access(epm, team_user, has_access=True)

    # The user should be able to access the components because he has access to the product
    assert (
        user.get("/api/v1/topics/%s/components" % rhel_81_topic["id"]).status_code
        == 200
    )

    # epm remove the RHEL product permission
    deny_team_to_access_product(epm, team_user["id"], rhel_product["id"])

    # The user can't see the components now
    assert (
        user.get("/api/v1/topics/%s/components" % rhel_81_topic["id"]).status_code
        == 401
    )


def test_components_export_control_true(admin, user, rhel_80_topic, rhel_80_component):
    assert rhel_80_topic["export_control"]

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
        c_file = admin.post(url, data="lol")
        c_file_1_id = c_file.data["component_file"]["id"]
        # team_user has not access to pre release content but it's
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
    admin, user, team_user, rhel_product, rhel_81_topic, rhel_81_component
):
    assert rhel_81_topic["export_control"] is False
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
        c_file = admin.post(url, data="lol")
        c_file_1_id = c_file.data["component_file"]["id"]

        # allow team to download pre release content
        team_user = change_team_pre_release_access(admin, team_user, has_access=True)
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

        # remove pre release content access
        change_team_pre_release_access(admin, team_user, has_access=False)

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
