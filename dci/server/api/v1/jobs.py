# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Red Hat, Inc
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
import sqlalchemy.sql

from dci.server.api.v1 import api
from dci.server.api.v1 import utils as v1_utils
from dci.server import auth2
from dci.server.common import exceptions as dci_exc
from dci.server.common import schemas
from dci.server.common import utils
from dci.server.db import models_core as models

from dci.server.api.v1 import jobstates

# associate column names with the corresponding SA Column object
_JOBS_COLUMNS = v1_utils.get_columns_name_with_objects(models.JOBS)
_VALID_EMBED = {'jobdefinition': models.JOBDEFINITIONS,
                # TODO(spredzy) : Remove this when the join and multiple
                # entities is supported
                'jobdefinition.jobdefinition_component':
                models.JOIN_JOBDEFINITIONS_COMPONENTS,
                'jobdefinition.test': models.TESTS,
                'team': models.TEAMS,
                'remoteci': models.REMOTECIS}


def _verify_existence_and_get_job(job_id):
    return v1_utils.verify_existence_and_get(
        [models.JOBS], job_id, models.JOBS.c.id == job_id)


@api.route('/jobs', methods=['POST'])
@auth2.requires_auth
def create_jobs(user):
    values = schemas.job.post(flask.request.json)

    # If it's not a super admin nor belongs to the same team_id
    auth2.is_admin_or_in_same_team(user, values['team_id'])

    etag = utils.gen_etag()
    values.update({
        'id': utils.gen_uuid(),
        'created_at': datetime.datetime.utcnow().isoformat(),
        'updated_at': datetime.datetime.utcnow().isoformat(),
        'etag': etag,
        'recheck': values.get('recheck', False)
    })

    query = models.JOBS.insert().values(**values)

    flask.g.db_conn.execute(query)

    return flask.Response(json.dumps({'job': values}), 201,
                          headers={'ETag': etag},
                          content_type='application/json')


@api.route('/jobs', methods=['GET'])
@auth2.requires_auth
def get_all_jobs(user, jd_id=None):
    """Get all jobs.

    If jd_id is not None, then return all the jobs with a jobdefinition
    pointed by jd_id.
    """
    # get the diverse parameters
    args = schemas.args(flask.request.args.to_dict())
    # convenient alias
    embed = args['embed']

    # the default query with no parameters
    query = sqlalchemy.sql.select([models.JOBS])

    # if embed then construct the query with a join
    if embed:
        query = v1_utils.get_query_with_join(models.JOBS, [models.JOBS],
                                             embed, _VALID_EMBED)

    if not auth2.is_admin(user):
        query = query.where(models.JOBS.c.team_id == user['team_id'])

    query = v1_utils.sort_query(query, args['sort'], _JOBS_COLUMNS)
    query = v1_utils.where_query(query, args['where'], models.JOBS,
                                 _JOBS_COLUMNS)

    # used for counting the number of rows when jd_id is not None
    where_jd_cond = None
    if jd_id is not None:
        where_jd_cond = models.JOBS.c.jobdefinition_id == jd_id
        query = query.where(where_jd_cond)

    # adds the limit/offset parameters
    if args['limit'] is not None:
        query = query.limit(args['limit'])

    if args['offset'] is not None:
        query = query.offset(args['offset'])

    # get the number of rows for the '_meta' section
    nb_row = utils.get_number_of_rows(models.JOBS, where_jd_cond)

    rows = flask.g.db_conn.execute(query).fetchall()
    result = [v1_utils.group_embedded_resources(embed, row) for row in rows]

    result = {'jobs': result, '_meta': {'count': nb_row}}
    result = json.dumps(result, default=utils.json_encoder)
    return flask.Response(result, 200, content_type='application/json')


@api.route('/jobs/<j_id>/jobstates', methods=['GET'])
@auth2.requires_auth
def get_jobstates_by_job(user, j_id):
    _verify_existence_and_get_job(j_id)
    return jobstates.get_all_jobstates(j_id=j_id)


@api.route('/jobs/<jd_id>', methods=['GET'])
@auth2.requires_auth
def get_job_by_id(user, jd_id):
    # get the diverse parameters
    embed = schemas.args(flask.request.args.to_dict())['embed']
    v1_utils.verify_embed_list(embed, _VALID_EMBED.keys())

    # the default query with no parameters
    query = sqlalchemy.sql.select([models.JOBS])

    # if embed then construct the query with a join
    if embed:
        query = v1_utils.get_query_with_join(models.JOBS, [models.JOBS],
                                             embed, _VALID_EMBED)

    if not auth2.is_admin(user):
        query = query.where(models.JOBS.c.team_id == user['team_id'])

    query = query.where(models.JOBS.c.id == jd_id)

    row = flask.g.db_conn.execute(query).fetchone()
    job = v1_utils.group_embedded_resources(embed, row)

    if row is None:
        raise dci_exc.DCIException("Job '%s' not found." % jd_id,
                                   status_code=404)

    etag = job['etag']
    job = json.dumps({'job': job}, default=utils.json_encoder)
    return flask.Response(job, 200, headers={'ETag': etag},
                          content_type='application/json')


@api.route('/jobs/<j_id>/recheck', methods=['POST'])
@auth2.requires_auth
def job_recheck(user, j_id):

    job_to_recheck = dict(_verify_existence_and_get_job(j_id))
    auth2.is_admin_or_in_same_team(user, job_to_recheck['team_id'])
    etag = utils.gen_etag()
    values = utils.dict_merge(job_to_recheck, {
        'id': utils.gen_uuid(),
        'created_at': datetime.datetime.utcnow().isoformat(),
        'updated_at': datetime.datetime.utcnow().isoformat(),
        'etag': etag,
        'recheck': True,
    })
    query = models.JOBS.insert().values(**values)

    flask.g.db_conn.execute(query)

    return flask.Response(json.dumps({'job': values}), 201,
                          headers={'ETag': etag},
                          content_type='application/json')


@api.route('/jobs/<jd_id>', methods=['DELETE'])
@auth2.requires_auth
def delete_job_by_id(user, jd_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    job = dict(_verify_existence_and_get_job(jd_id))

    auth2.is_admin_or_in_same_team(user, job['team_id'])

    where_clause = sqlalchemy.sql.and_(models.JOBS.c.id == jd_id,
                                       models.JOBS.c.etag == if_match_etag)
    query = models.JOBS.delete().where(where_clause)

    result = flask.g.db_conn.execute(query)

    if result.rowcount == 0:
        raise dci_exc.DCIException("Job '%s' already deleted or "
                                   "etag not matched." % jd_id,
                                   status_code=409)

    return flask.Response(None, 204, content_type='application/json')
