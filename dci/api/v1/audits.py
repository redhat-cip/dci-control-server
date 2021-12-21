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

import flask

from dci.api.v1 import api
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.db import models2
from dci.db import declarative

from dci.common.schemas import check_and_get_args


@api.route("/audits", methods=["GET"])
@decorators.login_required
def get_logs(user):
    args = check_and_get_args(flask.request.args.to_dict())

    query = flask.g.session.query(models2.Log)
    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    nb_logs = query.count()
    query = declarative.handle_args(query, models2.Log, args)
    audits = [
        {
            "id": audit.id,
            "created_at": audit.created_at,
            "user_id": audit.user_id,
            "action": audit.action,
        }
        for audit in query.all()
    ]
    return flask.jsonify({"audits": audits, "_meta": {"count": nb_logs}})
