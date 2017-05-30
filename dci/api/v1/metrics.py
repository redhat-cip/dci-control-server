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
from dci import auth
from dci.db import models


@api.route('/metrics', methods=['GET'])
@auth.login_required
def get_all_metrics(user):
    if not auth.is_admin(user):
        raise auth.UNAUTHORIZED

    data = {}
    stmt = (sql.select([models.TOPICS.c.id,
                        models.TOPICS.c.name])
            .select_from(models.TOPICS)
            .where(models.TOPICS.c.state == 'active')
            .order_by(models.TOPICS.c.name))
    topics = flask.g.db_conn.execute(stmt).fetchall()
    for t in topics:
        data[t['name']] = list()
        stmt = (sql.select([models.COMPONENTS.c.name,
                            models.COMPONENTS.c.created_at])
                .select_from(models.COMPONENTS)
                .where(
                    sql.and_(
                        models.COMPONENTS.c.topic_id == t['id'],
                        models.COMPONENTS.c.state == 'active'))
                .order_by(models.COMPONENTS.c.created_at.asc()))
        components = flask.g.db_conn.execute(stmt).fetchall()
        for i, c in enumerate(components):
            if i == len(components) - 1:
                next_item = {'created_at': models.datetime.datetime.utcnow()}
            else:
                next_item = components[i + 1]
            stmt = (sql.select([models.JOBS.c.id,
                                models.JOBS.c.created_at])
                    .select_from(
                        sql.join(
                            models.JOBS,
                            models.JOBDEFINITIONS))
                    .where(
                        sql.and_(
                            models.JOBS.c.state == 'active',
                            models.JOBDEFINITIONS.c.topic_id == t['id'],
                            sql.between(models.JOBS.c.created_at,
                                        c['created_at'],
                                        next_item['created_at'])))
                    .order_by(models.JOBS.c.created_at))
            jobs = flask.g.db_conn.execute(stmt).fetchall()
            if not jobs:
                first = 'None'
                last = 'None'
            else:
                first = jobs[0]['created_at'] - c['created_at']
                last = models.datetime.datetime.utcnow() - jobs[-1]['created_at']  # noqa
                first = str(first.total_seconds() / 3600)
                last = str(last.total_seconds() / 3600)
            data[t['name']].append({'component': c['name'],
                                    'date': c['created_at'],
                                    'values': [first, last]})

    return flask.jsonify({'topics': data,
                          '_meta': {'count': len(topics)}})
