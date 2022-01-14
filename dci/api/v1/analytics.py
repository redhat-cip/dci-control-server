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
import json
import logging
import requests
from requests.exceptions import ConnectionError

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import export_control
from dci.common import exceptions as dci_exc
from dci.common.schemas import (
    analytics_task_duration_cumulated,
    analytics_task_components_coverage,
    check_json_is_valid,
)
from dci.dci_config import CONFIG
from dci.db import models2
from dci import decorators

logger = logging.getLogger(__name__)


@api.route("/analytics/tasks_duration_cumulated", methods=["GET"])
@decorators.login_required
def tasks_duration_cumulated(user):
    args = flask.request.args.to_dict()
    check_json_is_valid(analytics_task_duration_cumulated, args)
    topic = base.get_resource_orm(models2.Topic, args["topic_id"])
    remoteci = base.get_resource_orm(models2.Remoteci, args["remoteci_id"])

    if user.is_not_super_admin() and user.is_not_epm() and user.is_not_read_only_user():
        if remoteci.team_id not in user.teams_id:
            raise dci_exc.Unauthorized()
    export_control.verify_access_to_topic(user, topic)

    query = "q=topic_id:%s AND remoteci_id:%s" % (args["topic_id"], args["remoteci_id"])

    try:
        res = requests.get(
            "%s/tasks_duration_cumulated/_search?%s"
            % (CONFIG["ELASTICSEARCH_URL"], query)
        )
        if res.status_code == 200:
            return flask.jsonify(res.json()["hits"])
        elif res.status_code == 404:
            return flask.Response(
                json.dumps({"error": "ressource not found in backend service"}),
                404,
                content_type="application/json",
            )
        else:
            logger.error("analytics error: %s" % str(res.text))
            return flask.Response(
                json.dumps({"error": "error with backend service"}),
                res.status_code,
                content_type="application/json",
            )
    except ConnectionError as e:
        logger.error("analytics error: %s" % str(e))
        return flask.Response(
            json.dumps({"error": "connection error with backend service"}),
            503,
            content_type="application/json",
        )


@api.route("/analytics/tasks_components_coverage", methods=["GET"])
@decorators.login_required
def tasks_components_coverage(user):
    args = flask.request.args.to_dict()
    check_json_is_valid(analytics_task_components_coverage, args)

    team_id = args.get("team_id") if args.get("team_id") else "red_hat"
    topic_id = args["topic_id"]

    if user.is_not_super_admin() and user.is_not_epm() and user.is_not_read_only_user():
        if team_id not in user.teams_id:
            raise dci_exc.Unauthorized()

    query = "q=topic_id:%s AND team_id:%s" % (topic_id, team_id)

    try:
        res = requests.get(
            "%s/tasks_components_coverage/_search?%s"
            % (CONFIG["ELASTICSEARCH_URL"], query),
            headers={"Content-Type": "application/json"},
            data=json.dumps({"sort": [{"component_name": {"order": "asc"}}]}),
        )

        if res.status_code == 200:
            return flask.jsonify(res.json()["hits"])
        elif res.status_code == 404:
            return flask.Response(
                json.dumps({"error": "ressource not found in backend service"}),
                404,
                content_type="application/json",
            )
        else:
            logger.error("analytics error: %s" % str(res.text))
            return flask.Response(
                json.dumps({"error": "error with backend service"}),
                res.status_code,
                content_type="application/json",
            )
    except ConnectionError as e:
        logger.error("analytics error: %s" % str(e))
        return flask.Response(
            json.dumps({"error": "connection error with backend service"}),
            503,
            content_type="application/json",
        )
