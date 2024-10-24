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

import os

import flask
import logging
import requests

from dci.api.v2 import api
from dci.api.v1 import base
from dci.api.v1.components import _verify_component_and_topic_access
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.dci_config import CONFIG
from dci.db import models2
from dciauth.signature import HmacAuthBase


logger = logging.getLogger(__name__)


@api.route("/components/<uuid:c_id>/files/<path:filepath>", methods=["GET", "HEAD"])
@decorators.login_required
def get_component_file_from_rhdl(user, c_id, filepath):
    component = base.get_resource_orm(models2.Component, c_id)
    _verify_component_and_topic_access(user, component)

    if filepath == "dci_files_list.json":
        filepath = "rhdl_files_list.json"
    normalized_filepath = os.path.normpath("/" + filepath).lstrip("/")
    normalized_rhdl_component_filepath = os.path.join(
        component.display_name, "files", normalized_filepath
    )
    rhdl_component_filepath = os.path.join(component.display_name, "files", filepath)
    if rhdl_component_filepath != normalized_rhdl_component_filepath:
        raise dci_exc.DCIException("Request malformed: filepath is invalid")

    rhdl_file_url = os.path.join(
        CONFIG["RHDL_API_URL"], "components", normalized_rhdl_component_filepath
    )
    auth = HmacAuthBase(
        access_key=CONFIG["RHDL_SERVICE_ACCOUNT_ACCESS_KEY"],
        secret_key=CONFIG["RHDL_SERVICE_ACCOUNT_SECRET_KEY"],
        region="us-east-1",
        service="api",
        service_key="aws4_request",
        algorithm="AWS4-HMAC-SHA256",
    )
    redirect = requests.get(
        rhdl_file_url,
        allow_redirects=False,
        auth=auth,
        timeout=CONFIG["REQUESTS_TIMEOUT"],
    )
    if redirect.status_code != 302:
        raise dci_exc.DCIException(
            message=redirect.content, status_code=redirect.status_code
        )

    return flask.Response(None, 302, headers={"Location": redirect.headers["Location"]})
