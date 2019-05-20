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
from dci.common import exceptions as dci_exc
from dci.common.schemas import (
    check_json_is_valid,
    counter_schema,
    check_and_get_args
)
from dci.common import utils
from dci.db import models

from sqlalchemy import sql, func


_TABLE = models.JOBS_EVENTS
_JOBS_EVENTS_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)


@api.route('/jobs_events/<int:sequence>', methods=['GET'])
@decorators.login_required
def get_jobs_events_from_sequence(user, sequence):
    """Get all the jobs events from a given sequence number."""

    args = check_and_get_args(flask.request.args.to_dict())

    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    query = sql.select([models.JOBS_EVENTS]). \
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

    query_nb_rows = sql.select([func.count(models.JOBS_EVENTS.c.id)])
    nb_rows = flask.g.db_conn.execute(query_nb_rows).scalar()

    return json.jsonify({'jobs_events': rows, '_meta': {'count': nb_rows}})


@api.route('/jobs_events/<int:sequence>', methods=['DELETE'])
@decorators.login_required
def purge_jobs_events_from_sequence(user, sequence):
    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()
    query = _TABLE.delete(). \
        where(_TABLE.c.id >= sequence)
    flask.g.db_conn.execute(query)

    return flask.Response(None, 204, content_type='application/json')


def create_event(job_id, status, topic_id=None):
    values = {'job_id': str(job_id),
              'status': status,
              'topic_id': str(topic_id)}
    if not topic_id:
        job = v1_utils.verify_existence_and_get(job_id, models.JOBS)
        job = dict(job)
        values['topic_id'] = str(job['topic_id'])
    q_add_job_event = models.JOBS_EVENTS.insert().values(**values)
    flask.g.db_conn.execute(q_add_job_event)


@api.route('/jobs_events/sequence', methods=['GET'])
@decorators.login_required
def get_current_sequence(user):
    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    def create_sequence():
        etag = utils.gen_etag()
        q_add_counter = models.COUNTER.insert().values(name='jobs_events',
                                                       sequence=0,
                                                       etag=etag)
        flask.g.db_conn.execute(q_add_counter)

    def get_sequence():
        query = sql.select([models.COUNTER]).\
            where(models.COUNTER.c.name == 'jobs_events')
        return flask.g.db_conn.execute(query).fetchone()

    je_sequence = get_sequence()
    if not je_sequence:
        create_sequence()
        je_sequence = get_sequence()

    return json.jsonify({'sequence': {'sequence': je_sequence.sequence,
                                      'etag': je_sequence.etag}})


@api.route('/jobs_events/sequence', methods=['PUT'])
@decorators.login_required
def put_current_sequence(user):
    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    values = flask.request.json
    check_json_is_valid(counter_schema, values)
    etag = utils.gen_etag()
    q_update = models.COUNTER.update().\
        where(sql.and_(models.COUNTER.c.name == 'jobs_events',
                       models.COUNTER.c.etag == if_match_etag)).\
        values(sequence=values['sequence'],
               etag=etag)
    result = flask.g.db_conn.execute(q_update)
    if not result.rowcount:
        raise dci_exc.DCIConflict('jobs_events', 'sequence')

    return flask.Response(None, 204, content_type='application/json')
