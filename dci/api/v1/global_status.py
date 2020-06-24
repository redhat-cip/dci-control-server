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
from dci.api.v1 import components as v1_components
from dci import decorators


def insert_component_with_no_job(components, latest_components):

    component_names = [component['topic_name'] for component in components]

    for component in latest_components:
        if component['topic_name'] not in component_names:
            components.append({
                'id': component['id'],
                'name': component['name'],
                'topic_name': component['topic_name'],
                'product_name': component['product_name'],
                'jobs': []
            })

    return components


def format_global_status(jobs):
    components = {}
    for job in jobs:
        component_id = job['component_id']
        component = components.get(component_id, {
            'id': component_id,
            'name': job['component_name'],
            'topic_name': job['topic_name'],
            'product_name': job['product_name'],
            'jobs': []
        })
        component['jobs'].append({
            'id': job['id'],
            'team_name': job['team_name'],
            'remoteci_name': job['remoteci_name'],
            'status': job['status'],
            'created_at': job['created_at'],
        })
        components[component_id] = component
    return list(components.values())


def add_percentage_of_success(global_status):
    for component in global_status:
        nb_of_success = 0
        for job in component['jobs']:
            if job['status'] == 'success':
                nb_of_success += 1
        success = 0
        if len(component['jobs']):
            success = int(round(100 * nb_of_success / len(component['jobs'])))
        component['percentageOfSuccess'] = success
    return global_status


@api.route('/global_status', methods=['GET'])
@decorators.login_required
def get_global_status(user):
    sql = text("""
SELECT DISTINCT ON (components.id, jobs.remoteci_id)
    jobs.id,
    jobs.status,
    jobs.created_at,
    jobs.remoteci_id,
    components.id as component_id,
    components.name as component_name,
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
LEFT JOIN jobs_components ON jobs.id = jobs_components.job_id
LEFT JOIN components ON components.id = jobs_components.component_id
LEFT JOIN products ON topics.product_id = products.id
WHERE
    teams.external = '1' AND
    (jobs.status = 'failure' OR jobs.status = 'success') AND
    remotecis.state = 'active' AND
    components.id IN (SELECT DISTINCT ON (topic_id) id
                      FROM components
                      WHERE state = 'active'
                      ORDER BY topic_id, created_at DESC)
ORDER BY
    components.id,
    jobs.remoteci_id,
    jobs.created_at DESC;
""")  # noqa

    jobs = flask.g.db_conn.execute(sql)
    global_status = format_global_status(jobs)
    global_status = insert_component_with_no_job(
        global_status, v1_components._get_latest_components()
    )
    return flask.jsonify(
        {'globalStatus': add_percentage_of_success(global_status)}
    )
