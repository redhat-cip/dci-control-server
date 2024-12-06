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

import flask

from dci.api.v2 import api
from dci.api.v1 import base
from dci import decorators
from dci.common import exceptions as dci_exc

from dci.db import models2
from dci.stores import files_utils
import logging

logger = logging.getLogger(__name__)


@api.route("/files/<uuid:file_id>/content", methods=["GET", "HEAD"])
@decorators.login_required
def get_file_content_from_s3(user, file_id):
    file = base.get_resource_orm(models2.File, file_id)
    if (
        user.is_not_in_team(file.team_id)
        and user.is_not_read_only_user()
        and user.is_not_epm()
    ):
        raise dci_exc.Unauthorized()

    file_path = files_utils.build_file_path(file.team_id, file.job_id, file.id)

    presign_url_method = "get_object"
    if flask.request.method == "HEAD":
        presign_url_method = "head_object"

    presigned_url = flask.g.store.get_presigned_url(
        presign_url_method, "files", file_path
    )

    return flask.Response(
        None, 302, content_type="application/json", headers={"Location": presigned_url}
    )
