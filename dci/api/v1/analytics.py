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
import uuid

from dci.analytics import query_es_dsl as qed
from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import permissions
from dci.common import exceptions as dci_exc
from dci.common.schemas import (
    analytics_task_duration_cumulated,
    analytics_task_components_coverage,
    analytics_tasks_junit,
    analytics_tasks_pipelines_status,
    check_json_is_valid,
)
from dci.dci_config import CONFIG
from dci.db import models2
from dci import decorators

logger = logging.getLogger(__name__)


def handle_pagination(args):
    limit_max = 200
    default_limit = 20
    default_offset = 0
    offset = int(args.get("offset", default_offset))
    limit = min(int(args.get("limit", default_limit)), limit_max)
    return (offset, limit)


@api.route("/analytics/tasks_duration_cumulated", methods=["GET"])
@decorators.login_required
def tasks_duration_cumulated(user):
    args = flask.request.args.to_dict()
    check_json_is_valid(analytics_task_duration_cumulated, args)
    topic = base.get_resource_orm(models2.Topic, args["topic_id"])
    remoteci = base.get_resource_orm(models2.Remoteci, args["remoteci_id"])

    if user.is_not_super_admin() and user.is_not_epm() and user.is_not_read_only_user():
        if remoteci.team_id not in user.teams_ids:
            raise dci_exc.Unauthorized()
    permissions.verify_access_to_topic(user, topic)

    query = "q=topic_id:%s AND remoteci_id:%s" % (args["topic_id"], args["remoteci_id"])
    offset, limit = handle_pagination(args)
    try:
        res = requests.get(
            "%s/elasticsearch/tasks_duration_cumulated/_search?%s"
            % (CONFIG["ANALYTICS_URL"], query),
            headers={"Content-Type": "application/json"},
            data=json.dumps(
                {
                    "from": offset,
                    "size": limit,
                    "sort": [{"created_at": {"order": "desc"}}],
                }
            ),
        )

        if res.status_code == 200:
            return flask.jsonify(res.json()["hits"])
        elif res.status_code == 404:
            raise dci_exc.DCIException(
                "resource not found in backend server: %s" % res.text, status_code=404
            )
        else:
            logger.error("analytics error: %s" % res.text)
            raise dci_exc.DCIException(
                "error with backend service: %s" % res.text, status_code=res.status_code
            )
    except ConnectionError as e:
        logger.error("analytics connection error: %s " % str(e))
        raise dci_exc.DCIException(
            "connection error with backend service", status_code=503
        )


@api.route("/analytics/tasks_components_coverage", methods=["GET"])
@decorators.login_required
def tasks_components_coverage(user):
    args = flask.request.args.to_dict()
    check_json_is_valid(analytics_task_components_coverage, args)
    types = flask.request.args.getlist("types")

    topic_id = args["topic_id"]

    if user.is_not_super_admin() and user.is_not_epm() and user.is_not_read_only_user():
        team_id = args.get("team_id")
        if not team_id:
            raise dci_exc.DCIException(
                "team_id argument is mandatory for regular users",
            )
        if uuid.UUID(team_id) not in user.teams_ids:
            raise dci_exc.Unauthorized()
    else:
        team_id = args.get("team_id") if args.get("team_id") else "red_hat"

    query = {
        "size": 10000,
        "query": {
            "bool": {
                "must": [
                    {"term": {"topic_id": topic_id}},
                    {"term": {"team_id": team_id}},
                ]
            }
        },
        "sort": [
            {
                "released_at": {
                    "order": "desc",
                    "format": "strict_date_optional_time_nanos",
                }
            }
        ],
    }
    if types:
        bool_should = {"bool": {"should": []}}
        for t in types:
            bool_should["bool"]["should"].append({"term": {"type": t}})
        query["query"]["bool"]["must"].append(bool_should)
    else:
        # returns only one unique component for each type (with latest first)
        query["collapse"] = {"field": "type"}

    try:
        res = requests.get(
            "%s/elasticsearch/tasks_components_coverage/_search"
            % (CONFIG["ANALYTICS_URL"]),
            headers={"Content-Type": "application/json"},
            json=query,
        )

        if res.status_code == 200:
            return flask.jsonify(res.json()["hits"])
        elif res.status_code == 404:
            raise dci_exc.DCIException(
                "resource not found in backend server: %s" % res.text, status_code=404
            )
        else:
            logger.error("analytics error: %s" % res.text)
            raise dci_exc.DCIException(
                "error with backend service: %s" % res.text, status_code=res.status_code
            )
    except ConnectionError as e:
        logger.error("analytics connection error: %s" % str(e))
        raise dci_exc.DCIException(
            "connection error with backend service", status_code=503
        )


@api.route("/analytics/junit_comparison", methods=["POST"])
@decorators.login_required
def tasks_junit_comparison(user):
    values = flask.request.json
    check_json_is_valid(analytics_tasks_junit, values)

    remoteci_1 = base.get_resource_orm(models2.Remoteci, values["remoteci_1_id"])
    remoteci_2 = base.get_resource_orm(models2.Remoteci, values["remoteci_2_id"])

    if user.is_not_super_admin() and user.is_not_epm() and user.is_not_read_only_user():
        if (
            remoteci_1.team_id not in user.teams_ids
            or remoteci_2.team_id not in user.teams_ids
        ):
            raise dci_exc.Unauthorized()

    try:
        res = requests.post(
            "%s/analytics/junit_topics_comparison" % CONFIG["ANALYTICS_URL"],
            headers={"Content-Type": "application/json"},
            json=values,
        )

        if res.status_code == 200:
            return flask.jsonify(res.json())
        elif res.status_code == 404:
            raise dci_exc.DCIException(
                "resource not found in backend server: %s" % res.text, status_code=404
            )
        else:
            logger.error("analytics error: %s" % res.text)
            raise dci_exc.DCIException(
                "error with backend service: %s" % res.text, status_code=res.status_code
            )
    except ConnectionError as e:
        logger.error("analytics connection error: %s " % str(e))
        raise dci_exc.DCIException(
            "connection error with backend service", status_code=503
        )


@api.route("/analytics/pipelines_status", methods=["POST"])
@decorators.login_required
def tasks_pipelines_status(user):
    values = flask.request.json
    check_json_is_valid(analytics_tasks_pipelines_status, values)

    if user.is_not_super_admin() and user.is_not_epm() and user.is_not_read_only_user():
        if values["teams_ids"]:
            for team_id in values["teams_ids"]:
                if uuid.UUID(team_id) not in user.teams_ids:
                    raise dci_exc.Unauthorized()

    try:
        res = requests.post(
            "%s/analytics/pipelines_status" % CONFIG["ANALYTICS_URL"],
            headers={"Content-Type": "application/json"},
            json=values,
        )

        if res.status_code == 200:
            return flask.jsonify(res.json())
        else:
            logger.error("analytics error: %s" % str(res.text))
            return flask.Response(
                json.dumps({"error": "error with backend service: %s" % str(res.text)}),
                res.status_code,
                content_type="application/json",
            )
    except ConnectionError as e:
        logger.error("analytics connection error: %s" % str(e))
        return flask.Response(
            json.dumps({"error": "connection error with backend service: %s" % str(e)}),
            503,
            content_type="application/json",
        )


def handle_es_sort(args):
    field = args.get("sort")
    if not field:
        return [
            {"created_at": {"order": "desc", "format": "strict_date_optional_time"}}
        ]
    if field.startswith("-"):
        return [{field[1:]: {"order": "desc", "format": "strict_date_optional_time"}}]
    else:
        return [{field: {"order": "asc", "format": "strict_date_optional_time"}}]


def handle_es_timeframe(query, args):
    from_date = args.get("from")
    to_date = args.get("to")
    if from_date and to_date:
        return {
            "bool": {
                "filter": [
                    {"range": {"created_at": {"gte": from_date, "lte": to_date}}},
                    query,
                ]
            }
        }
    return query


def handle_includes_excludes(args):
    _source = {}
    excludes = args.get("excludes")
    if excludes:
        excludes = excludes.split(",")
        _source["excludes"] = excludes
    includes = args.get("includes")
    if includes:
        includes = includes.split(",")
        _source["includes"] = includes
    return _source


def build_es_query(args, teams_ids=None):
    es_query = {}

    offset, limit = handle_pagination(args)
    es_query["from"] = offset
    es_query["size"] = limit

    query_string = args.get("query")
    es_query["query"] = qed.build(query_string)
    es_query["query"] = handle_es_timeframe(es_query["query"], args)
    if teams_ids:
        es_query["query"] = {
            "bool": {
                "filter": [
                    {
                        "bool": {
                            "should": [
                                {"term": {"team_id": str(t_id)}} for t_id in teams_ids
                            ]
                        }
                    },
                    es_query["query"],
                ]
            }
        }

    es_query["sort"] = handle_es_sort(args)

    _source = handle_includes_excludes(args)
    if _source:
        es_query["_source"] = _source

    return es_query


@api.route("/analytics/jobs", methods=["GET", "POST"])
@decorators.login_required
def tasks_jobs(user):
    args = flask.request.args.to_dict()

    teams_ids = None
    if user.is_not_super_admin() and user.is_not_epm() and user.is_not_read_only_user():
        teams_ids = user.teams_ids

    try:
        es_query = build_es_query(args, teams_ids)
    except Exception as e:
        logger.error(f"error while building the elastic query: {e}")
        raise dci_exc.DCIException("syntax error while parsing the query")

    try:
        res = requests.get(
            "%s/analytics/jobs" % (CONFIG["ANALYTICS_URL"]),
            headers={"Content-Type": "application/json"},
            json=es_query,
        )
        res_json = res.json()

        if res.status_code == 200:
            return flask.jsonify(res_json)
        else:
            logger.error("analytics error: %s" % str(res.text))
            return flask.Response(
                json.dumps({"error": "error with backend service: %s" % str(res.text)}),
                res.status_code,
                content_type="application/json",
            )
    except ConnectionError as e:
        logger.error("analytics connection error: %s" % str(e))
        return flask.Response(
            json.dumps({"error": "connection error with backend service: %s" % str(e)}),
            503,
            content_type="application/json",
        )


def build_autocompletion_query(args, team_id):
    return {
        "field": args.get("field"),
        "team_id": team_id,
        "size": args.get("size", 10),
    }


@api.route("/analytics/jobs/autocomplete", methods=["GET", "POST"])
@decorators.login_required
def tasks_jobs_autocomplete(user):
    args = flask.request.args.to_dict()
    autocomplete = build_autocompletion_query(args, str(user.teams_ids[0]))

    try:
        res = requests.get(
            "%s/analytics/jobs/autocomplete" % (CONFIG["ANALYTICS_URL"]),
            headers={"Content-Type": "application/json"},
            json=autocomplete,
        )
        res_json = res.json()

        if res.status_code == 200:
            return flask.jsonify(res_json)
        else:
            logger.error("analytics error: %s" % str(res.text))
            return flask.Response(
                json.dumps({"error": "error with backend service: %s" % str(res.text)}),
                res.status_code,
                content_type="application/json",
            )
    except ConnectionError as e:
        logger.error("analytics connection error: %s" % str(e))
        return flask.Response(
            json.dumps({"error": "connection error with backend service: %s" % str(e)}),
            503,
            content_type="application/json",
        )


@api.route("/analytics/jobs2", methods=["GET", "POST"])
@decorators.login_required
def tasks_jobs2(user):
    if user.is_not_super_admin() and user.is_not_epm():
        raise dci_exc.Unauthorized()

    payload = flask.request.json

    try:
        res = requests.get(
            "%s/analytics/jobs" % (CONFIG["ANALYTICS_URL"]),
            headers={"Content-Type": "application/json"},
            json=payload,
        )

        if res.status_code == 200:
            return flask.jsonify(res.json())
        else:
            logger.error("analytics error: %s" % str(res.text))
            return flask.Response(
                json.dumps({"error": "error with backend service: %s" % str(res.text)}),
                res.status_code,
                content_type="application/json",
            )
    except ConnectionError as e:
        logger.error("analytics connection error: %s" % str(e))
        return flask.Response(
            json.dumps({"error": "connection error with backend service: %s" % str(e)}),
            503,
            content_type="application/json",
        )
