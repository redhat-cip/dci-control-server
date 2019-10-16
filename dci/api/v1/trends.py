# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Red Hat, Inc
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
import calendar

import flask
from sqlalchemy import text

from dci.api.v1 import api
from dci import decorators
from dci.dci_config import get_engine


def get_timestamp_of_the_day(datetime_object):
    midnight = datetime_object.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )
    return calendar.timegm(midnight.timetuple())


def get_trends_from_jobs(jobs):
    trends = dict()
    for job in jobs:
        topic_id = str(job['topic_id'])
        timestamp = get_timestamp_of_the_day(job['created_at'])
        trend = trends.get(topic_id, {})
        stats = trend.get(timestamp, {'success': 0, 'failure': 0})
        stats[job['status']] += 1
        trend[timestamp] = stats
        trends[topic_id] = trend

    results = dict()
    for topic_id, stats in trends.items():
        result = results.get(topic_id, [])
        for timestamp, stat in stats.items():
            result.append([int(timestamp), stat['success'], stat['failure']])
        results[topic_id] = result
    return results


@api.route('/trends/topics', methods=['GET'])
@decorators.login_required
def get_trends_of_topics(user):
    engine = get_engine()
    sql = text("""
SELECT jobs.id,
    jobs.status,
    jobs.created_at,
    jobs.topic_id
FROM jobs
LEFT JOIN teams ON jobs.team_id = teams.id
LEFT JOIN topics ON jobs.topic_id = topics.id
WHERE
    (jobs.status = 'failure' OR jobs.status = 'success') AND
    teams.external = true
ORDER BY jobs.created_at DESC;
    """)  # noqa

    jobs = engine.execute(sql)
    return flask.jsonify({'topics': get_trends_from_jobs(jobs)})
