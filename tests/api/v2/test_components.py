# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 Red Hat, Inc
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

import responses

from dci import dci_config


@responses.activate
def test_get_component_file_from_rhdl_user_team_in_RHEL_with_released_component(
    admin,
    remoteci_context,
    remoteci_user,
    rhel_product,
    rhel_80_component,
):
    rhdl_api_url = dci_config.CONFIG["RHDL_API_URL"]
    rhdl_composeinfo_url = (
        f"{rhdl_api_url}/components/{rhel_80_component['name']}/files/.composeinfo"
    )

    responses.add(
        method=responses.GET,
        url=rhdl_composeinfo_url,
        status=302,
        headers={
            "Location": "https://wedontcare",
        },
    )
    responses.add(
        method=responses.HEAD,
        url=rhdl_composeinfo_url,
        status=302,
        headers={
            "Location": "https://wedontcare",
        },
    )

    r = remoteci_context.get(
        f"/api/v2/components/{rhel_80_component['id']}/files/.composeinfo"
    )
    assert r.status_code == 302
    assert r.headers["Location"] is not None
    assert responses.assert_call_count(rhdl_composeinfo_url, 1) is True

    r = remoteci_context.head(
        f"/api/v2/components/{rhel_80_component['id']}/files/.composeinfo"
    )
    assert r.status_code == 302
    assert r.headers["Location"] is not None

    assert responses.assert_call_count(rhdl_composeinfo_url, 2) is True

    # delete product team permission
    r = admin.delete(
        "/api/v1/products/%s/teams/%s" % (rhel_product["id"], remoteci_user["team_id"]),
    )
    assert r.status_code == 204

    r = remoteci_context.get(
        "/api/v1/components/%s/files/.composeinfo" % rhel_80_component["id"]
    )
    assert r.status_code == 401

    r = remoteci_context.head(
        "/api/v1/components/%s/files/.composeinfo" % rhel_80_component["id"]
    )
    assert r.status_code == 401


@responses.activate
def test_get_files_list_from_rhdl_renames_files_list(
    remoteci_context,
    rhel_80_component,
):
    rhdl_api_url = dci_config.CONFIG["RHDL_API_URL"]
    rhdl_files_list_url = f"{rhdl_api_url}/components/{rhel_80_component['name']}/files/rhdl_files_list.json"
    responses.add(
        method=responses.GET,
        url=rhdl_files_list_url,
        status=302,
        headers={
            "Location": "https://wedontcare",
        },
    )

    r = remoteci_context.get(
        f"/api/v2/components/{rhel_80_component['id']}/files/dci_files_list.json"
    )
    assert r.status_code == 302
    assert r.headers["Location"] is not None
    assert responses.assert_call_count(rhdl_files_list_url, 1) is True
