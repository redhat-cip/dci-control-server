# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Red Hat, Inc
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

import datetime

import flask
from flask import json

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import notifications
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import models

# associate column names with the corresponding SA Column object
_TABLE = models.JOBSTATES
_JS_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)
_EMBED_MANY = {
    'team': False,
    'job': False,
    'files': True
}


def insert_jobstate(user, values, created_at=None):
    values.update({
        'id': utils.gen_uuid(),
        'created_at': created_at or datetime.datetime.utcnow().isoformat(),
        'team_id': user['team_id']
    })

    query = _TABLE.insert().values(**values)

    flask.g.db_conn.execute(query)


@api.route('/jobstates', methods=['POST'])
@decorators.login_required
def create_jobstates(user):
    created_at, _ = utils.get_dates(user)
    values = schemas.jobstate.post(flask.request.json)

    insert_jobstate(user, values, created_at)

    # Update job status
    job_id = values.get('job_id')
    query_update_job = (models.JOBS.update()
                        .where(models.JOBS.c.id == job_id)
                        .values(status=values.get('status')))
    result = flask.g.db_conn.execute(query_update_job)

    if not result.rowcount:
        raise dci_exc.DCIConflict('Job', job_id)

    FINAL_STATES = ['failure', 'success']
    if values.get('status') in FINAL_STATES:
        embeds = ['components', 'topic', 'remoteci']
        embeds_dict = {'components': True, 'topic': False, 'remoteci': False}

        job = v1_utils.verify_existence_and_get(job_id, models.JOBS)
        job = base.get_resource_by_id(user, dict(job), models.JOBS,
                                      embeds_dict, embeds=embeds,
                                      jsonify=False)
        job = dict(job)
        notifications.dispatcher(job)

    result = json.dumps({'jobstate': values})
    return flask.Response(result, 201, content_type='application/json')


@api.route('/jobstates', methods=['GET'])
@decorators.login_required
def get_all_jobstates(user, j_id=None):
    """Get all jobstates.
    """
    args = schemas.args(flask.request.args.to_dict())

    query = v1_utils.QueryBuilder(_TABLE, args, _JS_COLUMNS)
    if not user.is_super_admin() and not user.is_rh_employee():
        query.add_extra_condition(_TABLE.c.team_id.in_(user.teams))

    # used for counting the number of rows when j_id is not None
    if j_id is not None:
        query.add_extra_condition(_TABLE.c.job_id == j_id)

    # get the number of rows for the '_meta' section
    nb_rows = query.get_number_of_rows()
    rows = query.execute(fetchall=True)
    rows = v1_utils.format_result(rows, _TABLE.name, args['embed'],
                                  _EMBED_MANY)

    return flask.jsonify({'jobstates': rows, '_meta': {'count': nb_rows}})


@api.route('/jobstates/<uuid:js_id>', methods=['GET'])
@decorators.login_required
def get_jobstate_by_id(user, js_id):
    jobstate = v1_utils.verify_existence_and_get(js_id, _TABLE)
    return base.get_resource_by_id(user, jobstate, _TABLE, _EMBED_MANY)


@api.route('/jobstates/<uuid:js_id>', methods=['DELETE'])
@decorators.login_required
def delete_jobstate_by_id(user, js_id):
    jobstate = v1_utils.verify_existence_and_get(js_id, _TABLE)

    if not user.is_in_team(jobstate['team_id']):
        raise auth.UNAUTHORIZED

    where_clause = _TABLE.c.id == js_id
    query = _TABLE.delete().where(where_clause)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIDeleteConflict('Jobstate', js_id)

    return flask.Response(None, 204, content_type='application/json')
