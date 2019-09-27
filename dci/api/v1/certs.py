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
import os.path
from sqlalchemy import sql

from dci.api.v1 import api
from dci.api.v1.permissions import team_has_access_to_a_topic
from dci import decorators
from dci.db import models


def splitpath(path):
    path = os.path.normpath(path)
    paths = path.split("/")
    return [p for p in paths if p]


@api.route("/certs/verify", methods=["GET"])
@decorators.login_required
def verify_repo_access(user):
    headers = flask.request.headers
    verify = headers.get("SSLVerify")
    fp = headers.get("SSLFingerprint")
    url = headers.get("X-Original-URI")

    if verify != "SUCCESS":
        return flask.Response(None, 403)

    if len(splitpath(url)) < 3:
        return flask.Response(None, 403)

    product_id, topic_id, component_id = splitpath(url)[:3]

    query = sql.select([models.REMOTECIS]).where(models.REMOTECIS.c.cert_fp == fp)
    remoteci = flask.g.db_conn.execute(query).fetchone()
    if not remoteci:
        return flask.Response(None, 403)

    team_id = remoteci["team_id"]
    if not team_has_access_to_a_topic(team_id, product_id, topic_id):
        return flask.Response(None, 403)

    return flask.Response(None, 200)
