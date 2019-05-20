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

import flask

from flask import json
from sqlalchemy import sql
from sqlalchemy import exc as sa_exc
from dci.api.v1 import api
from dci.api.v1 import base
from dci import decorators
from dci.api.v1 import utils as v1_utils
from dci.common import exceptions as dci_exc
from dci.common.schemas2 import (
    check_json_is_valid,
    issue_schema,
    issue_test_schema,
    check_and_get_args
)
from dci.common import utils
from dci.db import models
from dci.trackers import github
from dci.trackers import bugzilla


_TABLE = models.ISSUES
_I_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)


def _get_or_create_issue(data):
    values = v1_utils.common_values_dict()
    values.update(data)
    if 'github.com' in values['url']:
        type = 'github'
    else:
        type = 'bugzilla'
    values['tracker'] = type

    # First, insert the issue if it doesn't already exist
    # in the issues table. If it already exists, ignore the
    # exceptions, and keep proceeding.
    query = _TABLE.insert().returning(*_TABLE.columns).values(**values)
    try:
        return flask.g.db_conn.execute(query).fetchone()
    except sa_exc.IntegrityError:
        # It is not a real failure it the issue have been tried
        # to inserted a second time. As long as it is once, we are
        # good to proceed
        query = (sql.select([_TABLE])
                 .where(sql.and_(_TABLE.c.url == values['url'],
                                 _TABLE.c.topic_id == values['topic_id'])))
        return flask.g.db_conn.execute(query).fetchone()


def get_issues_by_resource(resource_id, table):
    """Get all issues for a specific job."""

    v1_utils.verify_existence_and_get(resource_id, table)

    # When retrieving the issues for a job, we actually retrieve
    # the issues attach to the job itself + the issues attached to
    # the components the job has been run with.
    if table.name == 'jobs':
        JJI = models.JOIN_JOBS_ISSUES
        JJC = models.JOIN_JOBS_COMPONENTS
        JCI = models.JOIN_COMPONENTS_ISSUES

        # Get all the issues attach to all the components attach to a job
        j1 = sql.join(
            _TABLE,
            sql.join(
                JCI,
                JJC,
                sql.and_(
                    JCI.c.component_id == JJC.c.component_id,
                    JJC.c.job_id == resource_id,
                ),
            ),
            _TABLE.c.id == JCI.c.issue_id,
        )

        query = sql.select([_TABLE]).select_from(j1)
        rows = flask.g.db_conn.execute(query)
        rows = [dict(row) for row in rows]

        # Get all the issues attach to a job
        j2 = sql.join(
            _TABLE,
            JJI,
            sql.and_(
                _TABLE.c.id == JJI.c.issue_id,
                JJI.c.job_id == resource_id
            )
        )
        query2 = sql.select([_TABLE]).select_from(j2)
        rows2 = flask.g.db_conn.execute(query2)
        rows += [dict(row) for row in rows2]

    # When retrieving the issues for a component, we only retrieve the
    # issues attached to the specified component.
    else:
        JCI = models.JOIN_COMPONENTS_ISSUES

        query = (sql.select([_TABLE])
                 .select_from(JCI.join(_TABLE))
                 .where(JCI.c.component_id == resource_id))

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


def unattach_issue(resource_id, issue_id, table):
    """Unattach an issue from a specific job."""

    v1_utils.verify_existence_and_get(issue_id, _TABLE)
    if table.name == 'jobs':
        join_table = models.JOIN_JOBS_ISSUES
        where_clause = sql.and_(join_table.c.job_id == resource_id,
                                join_table.c.issue_id == issue_id)
    else:
        join_table = models.JOIN_COMPONENTS_ISSUES
        where_clause = sql.and_(join_table.c.component_id == resource_id,
                                join_table.c.issue_id == issue_id)

    query = join_table.delete().where(where_clause)
    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict('%s_issues' % table.name, issue_id)

    return flask.Response(None, 204, content_type='application/json')


def attach_issue(resource_id, table, user_id):
    data = flask.request.json
    check_json_is_valid(issue_schema, data)
    issue = _get_or_create_issue(data)

    # Second, insert a join record in the JOIN_JOBS_ISSUES or
    # JOIN_COMPONENTS_ISSUES database.
    if table.name == 'jobs':
        join_table = models.JOIN_JOBS_ISSUES
    else:
        join_table = models.JOIN_COMPONENTS_ISSUES

    key = '%s_id' % table.name[0:-1]
    query = join_table.insert().values({
        'user_id': user_id,
        'issue_id': issue['id'],
        key: resource_id
    })

    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(join_table.name,
                                          '%s, issue_id' % key)

    result = json.dumps({'issue': dict(issue)})
    return flask.Response(result, 201, content_type='application/json')


# CRD /issues
@api.route('/issues', methods=['POST'])
@decorators.login_required
def create_issue(user):
    data = flask.request.json
    check_json_is_valid(issue_test_schema, data)
    issue = _get_or_create_issue(data)
    result = json.dumps({'issue': dict(issue)})
    return flask.Response(result, 201,
                          headers={'ETag': issue['etag']},
                          content_type='application/json')


@api.route('/issues', methods=['GET'])
@decorators.login_required
def get_all_issues(user):
    args = check_and_get_args(flask.request.args.to_dict())

    query = v1_utils.QueryBuilder(_TABLE, args, _I_COLUMNS)
    query.add_extra_condition(_TABLE.c.state != 'archived')
    nb_rows = query.get_number_of_rows()
    rows = query.execute(fetchall=True)
    rows = v1_utils.format_result(rows, _TABLE.name)

    return flask.jsonify({'issues': rows, '_meta': {'count': nb_rows}})


@api.route('/issues/<uuid:issue_id>', methods=['GET'])
@decorators.login_required
def get_issue(user, issue_id):
    issue = v1_utils.verify_existence_and_get(issue_id, _TABLE)
    return flask.jsonify({'issue': issue})


@api.route('/issues/<uuid:issue_id>', methods=['DELETE'])
@decorators.login_required
def delete_issue_by_id(user, issue_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    v1_utils.verify_existence_and_get(issue_id, _TABLE)

    with flask.g.db_conn.begin():
        values = {'state': 'archived'}
        where_clause = sql.and_(
            _TABLE.c.etag == if_match_etag,
            _TABLE.c.id == issue_id
        )
        query = _TABLE.update().where(where_clause).values(**values)
        result = flask.g.db_conn.execute(query)
        if not result.rowcount:
            raise dci_exc.DCIDeleteConflict('Issue', issue_id)

    return flask.Response(None, 204, content_type='application/json')


# issues-tests
@api.route('/issues/<uuid:issue_id>/tests', methods=['POST'])
@decorators.login_required
def add_test_to_issue(user, issue_id):
    values = flask.request.json
    check_json_is_valid(issue_test_schema, values)

    issue_id = v1_utils.verify_existence_and_get(issue_id, _TABLE, get_id=True)

    values['issue_id'] = issue_id
    v1_utils.verify_existence_and_get(values.get('test_id'),
                                      models.TESTS,
                                      get_id=True)
    q_insert = models.JOIN_ISSUES_TESTS.insert().values(**values)
    flask.g.db_conn.execute(q_insert)
    return flask.Response(json.dumps(values),
                          201,
                          content_type='application/json')


@api.route('/issues/<uuid:issue_id>/tests/<uuid:test_id>', methods=['DELETE'])
@decorators.login_required
def remove_test_from_issue(users, issue_id, test_id):
    v1_utils.verify_existence_and_get(issue_id, _TABLE)
    v1_utils.verify_existence_and_get(test_id, models.TESTS)

    _JIT = models.JOIN_ISSUES_TESTS
    query = _JIT.delete().where(sql.and_(_JIT.c.issue_id == issue_id,
                                         _JIT.c.test_id == test_id))

    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCIDeleteConflict('tests', 'test_id')

    return flask.Response(None, 204, content_type='application/json')


@api.route('/issues/<uuid:issue_id>/tests', methods=['GET'])
@decorators.login_required
def get_tests_from_issue(user, issue_id):
    JIT = models.JOIN_ISSUES_TESTS

    query = (sql.select([models.TESTS])
                .select_from(JIT.join(models.TESTS))
                .where(JIT.c.issue_id == issue_id))

    results = flask.g.db_conn.execute(query).fetchall()

    return flask.Response(json.dumps({'tests': results}),
                          200,
                          content_type='application/json')


@api.route('/issues/purge', methods=['GET'])
@decorators.login_required
def get_to_purge_archived_issues(user):
    return base.get_to_purge_archived_resources(user, _TABLE)


@api.route('/issues/purge', methods=['POST'])
@decorators.login_required
def purge_archived_issues(user):
    return base.purge_archived_resources(user, _TABLE)
