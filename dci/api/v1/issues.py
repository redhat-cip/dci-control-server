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

from sqlalchemy import sql
from sqlalchemy import exc as sa_exc

from dci.api.v1 import utils as v1_utils
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import models


_TABLE = models.ISSUES
_VALID_EMBED = {
    'jobstate': v1_utils.embed(models.JOBSTATES),
    'jobstate.job': v1_utils.embed(models.JOBS),
    'team': v1_utils.embed(models.TEAMS)
}

def get_all_issues(job_id):
    v1_utils.verify_existence_and_get(job_id, models.JOBS)

    args = schemas.args(flask.request.args.to_dict())
    JJI = models.JOIN_JOBS_ISSUES

    query = (sql.select([_TABLE])
             .select_from(JJI.join(_TABLE))
             .where(JJI.c.job_id == job_id))
    rows = flask.g.db_conn.execute(query)

    return flask.jsonify({'issues': rows,
                          '_meta': {'count': rows.rowcount}})


def create_issue(job_id):
    values = flask.request.json

    if 'github.com' in values['url']:
        type = 'github'
    else :
        type = 'bugzilla'

    issue_id = utils.gen_uuid()
    values.update({
        'id': issue_id,
        'created_at': datetime.datetime.utcnow().isoformat(),
        'tracker': type,
        'status': 'new',
    })

    # First, insert the issue if it doesn't already exist
    # in the issues table. If it already exists, ignore the
    # exceptions, and keep proceeding.
    query = _TABLE.insert().values(**values)
    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        # It is not a real failure it the issue have been tried
        # to inserted a second time. As long as it is once, we are
        # good to proceed
        pass


    # Second, insert a join record in the JOIN_JOBS_ISSUES
    # database.
    values = {
        'job_id': job_id,
        'issue_id': issue_id
    }
    query = models.JOIN_JOBS_ISSUES.insert().values(**values)
    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise

    result = json.dumps(values)
    return flask.Response(result, 201, content_type='application/json')
