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
from dci.api.v1 import utils as v1_utils
from dci import decorators
from dci.db import models


def splitpath(path, maxdepth=20):
    (head, tail) = os.path.split(path)
    return splitpath(head, maxdepth - 1) + [tail] \
        if maxdepth and head and head != path \
        else [head or tail]


@api.route('/certs/verify', methods=['GET'])
@decorators.login_required
@decorators.check_roles
def verify_repo_access(user):
    headers = flask.request.headers
    verify = headers.get('SSLVerify')
    fp = headers.get('SSLFingerprint')
    url = headers.get('X-Original-URI')

    path = splitpath(url)
    path[:] = [item for item in path if item != '']

    if verify != "SUCCESS":
        return flask.Response(None, 403)

    if len(path) < 4:
        return flask.Response(None, 403)

    REMOTECIS = models.REMOTECIS
    query = (sql.select([REMOTECIS]).where(REMOTECIS.c.cert_fp == fp))
    remoteci = flask.g.db_conn.execute(query)

    if remoteci.rowcount != 1:
        return flask.Response(None, 403)

    v1_utils.verify_existence_and_get(path[1], models.PRODUCTS)
    v1_utils.verify_existence_and_get(path[2], models.TOPICS)
    v1_utils.verify_existence_and_get(path[3], models.COMPONENTS)

    team_id = remoteci.fetchone()['team_id']

    where_clause = sql.and_(
        models.TOPICS.c.state == 'active',
        models.TEAMS.c.state == 'active',
        models.COMPONENTS.c.state == 'active',
        models.JOINS_TOPICS_TEAMS.c.team_id == team_id,
        models.COMPONENTS.c.id == path[3],
        models.COMPONENTS.c.export_control,
        models.TOPICS.c.id == path[2]
    )
    query = (sql.select([models.JOINS_TOPICS_TEAMS.c.topic_id])
             .select_from(models.JOINS_TOPICS_TEAMS
                          .join(models.TOPICS).join(models.TEAMS)
                          .join(models.COMPONENTS))
             .where(where_clause))

    result = flask.g.db_conn.execute(query)

    if result.rowcount != 1:
        return flask.Response(None, 403)

    return flask.Response(None, 200)
