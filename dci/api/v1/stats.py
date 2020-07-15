# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Red Hat, Inc
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
from sqlalchemy import text

from dci.api.v1 import api
from dci import decorators


def _add_percentage_of_success(stats):
    for topic in stats:
        nb_of_success = 0
        for job in topic["jobs"]:
            if job["status"] == "success":
                nb_of_success += 1
        success = 0
        if len(topic["jobs"]):
            success = int(round(100 * nb_of_success / len(topic["jobs"])))
        topic["percentageOfSuccess"] = success
    return stats


def _format_stats(unsorted_jobs):
    topics = {}
    jobs = sorted(unsorted_jobs, key=lambda j: j["created_at"], reverse=True)
    for job in jobs:
        topic_id = job["topic_id"]
        topic = topics.get(
            topic_id,
            {
                "product": {"id": job["product_id"], "name": job["product_name"]},
                "percentageOfSuccess": 0,
                "jobs": [],
                "topic": {"id": topic_id, "name": job["topic_name"]},
            },
        )
        topic["jobs"].append(
            {
                "id": job["id"],
                "team_name": job["team_name"],
                "remoteci_name": job["remoteci_name"],
                "status": job["status"],
                "created_at": job["created_at"],
            }
        )
        topics[topic_id] = topic
    return _add_percentage_of_success(list(topics.values()))


def _build_team_query(user):
    team_query = "teams.state = 'active' AND teams.external = true"
    if user.is_not_read_only_user() and user.is_not_super_admin() and user.is_not_epm():
        teams_ids = ", ".join("'{0}'".format(str(i)) for i in user.teams_ids)
        team_query += " AND teams.id IN (%s)" % teams_ids
    return team_query


@api.route("/stats", methods=["GET"])
@decorators.login_required
def get_stats(user):
    sql = text(
        """
SELECT DISTINCT ON (topics.id , jobs.remoteci_id)
    jobs.id,
    jobs.status,
    jobs.created_at,
    jobs.remoteci_id,
    topics.id as topic_id,
    topics.name as topic_name,
    products.id as product_id,
    products.name as product_name,
    remotecis.name as remoteci_name,
    teams.name as team_name
FROM jobs
LEFT JOIN remotecis ON jobs.remoteci_id = remotecis.id
LEFT JOIN teams ON remotecis.team_id = teams.id
LEFT JOIN topics ON jobs.topic_id = topics.id
LEFT JOIN products ON topics.product_id = products.id
WHERE
    (jobs.status = 'failure' OR jobs.status = 'success') AND
    remotecis.state = 'active' AND
    topics.state = 'active' AND
    {team_query}
ORDER BY
    topics.id,
    jobs.remoteci_id,
    jobs.created_at DESC;
""".format(
            team_query=_build_team_query(user)
        )
    )

    jobs = flask.g.db_conn.execute(sql)
    return flask.jsonify({"stats": _format_stats(jobs)})
