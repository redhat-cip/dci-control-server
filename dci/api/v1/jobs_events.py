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
from flask import json

from dci.api.v1 import api
from dci.api.v1 import utils as v1_utils
from dci import decorators
from dci.common import schemas
from dci.db import models

from sqlalchemy import sql, func


_TABLE = models.JOBS_EVENTS
_JOBS_EVENTS_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)


@api.route('/jobs_events/<int:sequence>', methods=['GET'])
@decorators.login_required
@decorators.check_roles
def get_jobs_events_from_sequence(user, sequence):
    """Get all the jobs events from a given sequence number."""

    args = schemas.args(flask.request.args.to_dict())

    query = sql.select([models.JOBS_EVENTS, models.JOBS],
                       use_labels=True). \
        select_from(models.JOBS_EVENTS.join(models.JOBS,
                    models.JOBS.c.id == models.JOBS_EVENTS.c.job_id)). \
        where(_TABLE.c.id >= sequence)
    sort_list = v1_utils.sort_query(args['sort'], _JOBS_EVENTS_COLUMNS,
                                    default='created_at')
    query = v1_utils.add_sort_to_query(query, sort_list)

    if args.get('limit', None):
        query = query.limit(args.get('limit'))
    if args.get('offset', None):
        query = query.offset(args.get('offset'))

    rows = flask.g.db_conn.execute(query).fetchall()
    # res = []
    # for row in rows:
    #     row = dict(row)
    #     new_row = {}
    #     for field in row:
    #         if field.startswith('files_events'):
    #             suffix = field.split('files_events_')[1]
    #             if 'event' in new_row:
    #                 new_row['event'].update({suffix: row[field]})
    #             else:
    #                 new_row['event'] = {suffix: row[field]}
    #         else:
    #             suffix = field.split('files_')[1]
    #             if 'file' in new_row:
    #                 new_row['file'].update({suffix: row[field]})
    #             else:
    #                 new_row['file'] = {suffix: row[field]}
    #     res.append(new_row)

    query_nb_rows = sql.select([func.count(models.JOBS_EVENTS.c.id)])
    nb_rows = flask.g.db_conn.execute(query_nb_rows).scalar()

    return json.jsonify({'jobs_events': rows, '_meta': {'count': nb_rows}})


@api.route('/jobs_events/<int:sequence>', methods=['DELETE'])
@decorators.login_required
@decorators.check_roles
def purge_jobs_events_from_sequence(user, sequence):
    query = _TABLE.delete(). \
        where(_TABLE.c.id >= sequence)
    flask.g.db_conn.execute(query)

    return flask.Response(None, 204, content_type='application/json')


def create_event(job_id, status, topic_id=None):
    values = {'job_id': job_id,
              'status': status,
              'topic_id': topic_id}
    if topic_id is None:
        job = v1_utils.verify_existence_and_get(job_id, models.JOBS)
        job = dict(job)
        values['topic_id'] = job['topic_id']
    q_add_job_event = models.JOBS_EVENTS.insert().values(**values)
    flask.g.db_conn.execute(q_add_job_event)
