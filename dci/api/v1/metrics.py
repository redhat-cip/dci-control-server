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
from sqlalchemy import sql

from dci.api.v1 import api
from dci import decorators
from dci.db import models


def _get_all_topics():
    stmt = (sql.select([models.TOPICS.c.id,
                        models.TOPICS.c.name])
            .select_from(models.TOPICS)
            .where(models.TOPICS.c.state == 'active')
            .order_by(models.TOPICS.c.name))
    return flask.g.db_conn.execute(stmt).fetchall()


def _get_all_components_by_topic(topic_id):
    stmt = (sql.select([models.COMPONENTS.c.id,
                        models.COMPONENTS.c.name,
                        models.COMPONENTS.c.created_at])
            .select_from(models.COMPONENTS)
            .where(
                sql.and_(
                    models.COMPONENTS.c.topic_id == topic_id,
                    models.COMPONENTS.c.state == 'active'))
            .order_by(models.COMPONENTS.c.created_at.asc()))
    return flask.g.db_conn.execute(stmt).fetchall()


def _get_all_jobs_by_component(component_id):
    stmt = (sql.select([models.JOBS.c.created_at])
            .select_from(
                sql.join(
                    models.JOBS,
                    models.JOIN_JOBS_COMPONENTS))
            .where(
                sql.and_(
                    models.JOBS.c.state == 'active',
                    models.JOIN_JOBS_COMPONENTS.c.component_id == component_id))  # noqa
            .order_by(models.JOBS.c.created_at))
    return flask.g.db_conn.execute(stmt).fetchall()


@api.route('/metrics/topics', methods=['GET'])
@decorators.login_required
@decorators.has_role(['SUPER_ADMIN', 'PRODUCT_OWNER'])
def get_all_metrics(user):
    data = {}
    topics = _get_all_topics()
    for t in topics:
        data[t['name']] = []
        components = _get_all_components_by_topic(t['id'])
        for c in components:
            jobs = _get_all_jobs_by_component(c['id'])
            values = []
            for j in jobs:
                delay = j['created_at'] - c['created_at']
                values.append(int(delay.total_seconds()))
            data[t['name']].append({'component': c['name'],
                                    'date': c['created_at'],
                                    'values': values})

    return flask.jsonify({'topics': data,
                          '_meta': {'count': len(topics)}})
