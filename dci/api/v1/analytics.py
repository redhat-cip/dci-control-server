# -*- coding: utf-8 -*-
#
# Copyright (C) Red Hat, Inc
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

from dci.api.v1 import api
from dci.api.v1 import utils as v1_utils
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common import utils
from dci.db import models
from dci.common.schemas import (
    check_json_is_valid,
    create_analytic_schema,
    update_analytic_schema,
    check_and_get_args
)


_TABLE = models.ANALYTICS
_A_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)


@api.route('/jobs/<uuid:job_id>/analytics', methods=['POST'])
@decorators.login_required
def create_analytic(user, job_id):
    job = dict(v1_utils.verify_existence_and_get(job_id, models.JOBS))
    check_json_is_valid(create_analytic_schema, flask.request.json)
    values = flask.request.json
    values.update({
        'team_id': job['team_id'],
        'job_id': job_id
    })

    query = _TABLE.insert().returning(*_TABLE.columns).values(**values)
    result = flask.g.db_conn.execute(query)

    return flask.Response(json.dumps({'analytic': result.fetchone()}), 201,
                          content_type='application/json')


@api.route('/jobs/<uuid:job_id>/analytics', methods=['GET'])
@decorators.login_required
def get_all_analytics(user, job_id):
    v1_utils.verify_existence_and_get(job_id, models.JOBS)
    args = check_and_get_args(flask.request.args.to_dict())

    query = v1_utils.QueryBuilder(_TABLE, args, _A_COLUMNS)
    # If not admin nor rh employee then restrict the view to the team
    if (user.is_not_super_admin() and user.is_not_read_only_user() and
        user.is_not_epm()):
        query.add_extra_condition(_TABLE.c.team_id.in_(user.teams_ids))

    query.add_extra_condition(_TABLE.c.job_id == job_id)

    nb_rows = query.get_number_of_rows()
    rows = query.execute(fetchall=True)
    rows = v1_utils.format_result(rows, _TABLE.name)

    return flask.jsonify({'analytics': rows, '_meta': {'count': nb_rows}})


@api.route('/jobs/<uuid:job_id>/analytics/<uuid:anc_id>', methods=['GET'])
@decorators.login_required
def get_analytic(user, job_id, anc_id):
    v1_utils.verify_existence_and_get(job_id, models.JOBS)
    analytic = dict(v1_utils.verify_existence_and_get(anc_id, _TABLE))
    if not user.is_in_team(analytic['team_id']):
        raise dci_exc.Unauthorized()
    return flask.jsonify({'analytic': analytic})


@api.route('/jobs/<uuid:job_id>/analytics/<uuid:anc_id>', methods=['PUT'])
@decorators.login_required
def update_analytic(user, job_id, anc_id):
    job = v1_utils.verify_existence_and_get(job_id, models.JOBS)
    v1_utils.verify_existence_and_get(anc_id, _TABLE)
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    if not user.is_in_team(job['team_id']):
        raise dci_exc.Unauthorized()

    values = flask.request.json
    check_json_is_valid(update_analytic_schema, values)
    values.update({
        'etag': utils.gen_etag()
    })

    where_clause = sql.and_(
        _TABLE.c.etag == if_match_etag,
        _TABLE.c.id == anc_id
    )

    query = _TABLE.update().returning(*_TABLE.columns).where(where_clause). \
        values(**values)

    result = flask.g.db_conn.execute(query)
    if not result.rowcount:
        raise dci_exc.DCIConflict('Analytic', anc_id)

    return flask.Response(
        json.dumps({'analytic': result.fetchone()}), 200,
        headers={'ETag': values['etag']}, content_type='application/json'
    )


@api.route('/jobs/<uuid:job_id>/analytics/<uuid:anc_id>', methods=['DELETE'])
@decorators.login_required
def delete_analytics_by_id(user, job_id, anc_id):
    job = v1_utils.verify_existence_and_get(job_id, models.JOBS)
    v1_utils.verify_existence_and_get(anc_id, _TABLE)

    if not user.is_in_team(job['team_id']):
        raise dci_exc.Unauthorized()

    query = _TABLE.delete().where(_TABLE.c.id == anc_id)
    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIDeleteConflict('Analytic', anc_id)

    return flask.Response(None, 204, content_type='application/json')
