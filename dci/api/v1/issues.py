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
from dci.trackers import github
from dci.trackers import bugzilla


_TABLE = models.ISSUES


def get_all_issues(job_id):
    """Get all issues for a specific job."""

    v1_utils.verify_existence_and_get(job_id, models.JOBS)

    JJI = models.JOIN_JOBS_ISSUES

    query = (sql.select([_TABLE])
             .select_from(JJI.join(_TABLE))
             .where(JJI.c.job_id == job_id))
    rows = flask.g.db_conn.execute(query)
    rows = [dict(row) for row in rows]

    for row in rows:
        if row['tracker'] == 'github':
            l_tracker = github.Github(row['url'])
        elif row['tracker'] == 'bugzilla':
            l_tracker = bugzilla.Bugzilla(row['url'])
        row.update(l_tracker.dump())

    return flask.jsonify({'issues': rows,
                          '_meta': {'count': len(rows)}})


def unattach_issue(job_id, issue_id):
    """Unattach an issue from a specific job."""

    v1_utils.verify_existence_and_get(issue_id, _TABLE)
    JJI = models.JOIN_JOBS_ISSUES
    where_clause = sql.and_(JJI.c.job_id == job_id,
                            JJI.c.issue_id == issue_id)
    query = JJI.delete().where(where_clause)
    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict('Jobs_issues', issue_id)

    return flask.Response(None, 204, content_type='application/json')


def attach_issue(job_id):
    """Attach an issue to a specific job."""

    values = schemas.issue.post(flask.request.json)

    if 'github.com' in values['url']:
        type = 'github'
    else:
        type = 'bugzilla'

    issue_id = utils.gen_uuid()
    values.update({
        'id': issue_id,
        'created_at': datetime.datetime.utcnow().isoformat(),
        'tracker': type,
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
        raise dci_exc.DCICreationConflict(models.JOIN_JOBS_ISSUES.name,
                                          'job_id, issue_id')

    result = json.dumps(values)
    return flask.Response(result, 201, content_type='application/json')
