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
from dci.dci_config import generate_conf, get_engine


def filter_finished_jobs(jobs):
    filtered_jobs = []
    for job in jobs:
        if job['status'] in ['failure', 'success']:
            filtered_jobs.append(job)
    return filtered_jobs


def format_global_status(jobs):
    components = {}
    for job in jobs:
        component_id = job['component_id']
        component = components.get(component_id, {
            'id': component_id,
            'name': job['component_name'],
            'topic_name': job['topic_name'],
            'jobs': []
        })
        component['jobs'].append({
            'id': job['id'],
            'team_name': job['team_name'],
            'remoteci_name': job['remoteci_name'],
            'rconfiguration_name': job['rconfiguration_name'],
            'status': job['status'],
            'created_at': job['created_at'],
        })
        components[component_id] = component
    return components.values()


def add_percentage_of_success(global_status):
    for component in global_status:
        nb_of_success = 0
        for job in component['jobs']:
            if job['status'] == 'success':
                nb_of_success += 1
        success = int(round(100 * nb_of_success / len(component['jobs'])))
        component['percentageOfSuccess'] = success
    return global_status


@api.route('/global_status', methods=['GET'])
@decorators.login_required
@decorators.has_role(['SUPER_ADMIN', 'PRODUCT_OWNER'])
def get_global_status(user):
    conf = generate_conf()
    engine = get_engine(conf)
    sql = text("""
SELECT DISTINCT ON (jobs.remoteci_id, jobs.rconfiguration_id)
    remotecis.name as remoteci_name, teams.name as team_name, rconfigurations.name as rconfiguration_name, components.name as component_name, topics.name as topic_name, components.id as component_id, jobs.id, jobs.status, jobs.created_at, jobs.remoteci_id 
FROM jobs
LEFT JOIN remotecis ON jobs.remoteci_id = remotecis.id
LEFT JOIN teams ON remotecis.team_id = teams.id
LEFT JOIN topics ON jobs.topic_id = topics.id
LEFT JOIN rconfigurations ON jobs.rconfiguration_id = rconfigurations.id
LEFT JOIN jobs_components ON jobs.id = jobs_components.job_id
LEFT JOIN components ON components.id = jobs_components.component_id
WHERE teams.external = '1' AND remotecis.state = 'active' AND components.id IN (Select DISTINCT ON (topic_id) id from components ORDER By topic_id, created_at DESC) ORDER BY jobs.remoteci_id, jobs.rconfiguration_id, jobs.created_at DESC
""")  # noqa
    jobs = engine.execute(sql)
    filtered_jobs = filter_finished_jobs(jobs)
    global_status = format_global_status(filtered_jobs)
    return flask.jsonify(add_percentage_of_success(global_status))
