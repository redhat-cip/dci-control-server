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


@api.route('/global_status', methods=['GET'])
@decorators.login_required
@decorators.has_role(['SUPER_ADMIN', 'PRODUCT_OWNER'])
def get_global_status(user):
    conf = generate_conf()
    engine = get_engine(conf)
    latest_components_per_topic = text("""
SELECT DISTINCT ON (topic_id) topic_id, topics.name as topic_name, components.id, components.name, components.created_at
FROM components
JOIN topics ON components.topic_id = topics.id
ORDER BY topic_id, components.created_at DESC
""")  # noqa
    components = engine.execute(latest_components_per_topic)
    data = {}
    for component in components:
        data[component['name']] = dict(component)

        latest_jobs_per_remoteci_per_component = text("""
SELECT DISTINCT ON (jobs.remoteci_id) components.name, components.id, jobs.id, jobs.status, jobs.created_at, jobs.remoteci_id
FROM jobs
LEFT JOIN jobs_components ON jobs.id = jobs_components.job_id
LEFT JOIN components ON components.id = jobs_components.component_id
WHERE components.id = '%s' ORDER BY jobs.remoteci_id, jobs.created_at DESC;
        """ % component['id'])  # noqa
        jobs = engine.execute(latest_jobs_per_remoteci_per_component)
        data[component['name']]['jobs'] = jobs

    return flask.jsonify({'data': data})
