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
from sqlalchemy import sql

from dci.api.v1 import api
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import models

from dci.api.v1 import files
from dci.api.v1 import jobstates

_TABLE = models.JOBS
# associate column names with the corresponding SA Column object
_JOBS_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)
_VALID_EMBED = {
    'jobdefinition': models.JOBDEFINITIONS,
    # TODO(spredzy) : Remove this when the join and multiple
    # entities is supported
    'jobdefinition.jobdefinition_component':
        models.JOIN_JOBDEFINITIONS_COMPONENTS,
    'jobdefinition.test': models.TESTS,
    'team': models.TEAMS,
    'remoteci': models.REMOTECIS
}


@api.route('/jobs', methods=['POST'])
@auth.requires_auth
def create_jobs(user):
    values = schemas.job.post(flask.request.json)

    # If it's not a super admin nor belongs to the same team_id
    if not(auth.is_admin(user) or auth.is_in_team(user, values['team_id'])):
        raise auth.UNAUTHORIZED

    etag = utils.gen_etag()
    values.update({
        'id': utils.gen_uuid(),
        'created_at': datetime.datetime.utcnow().isoformat(),
        'updated_at': datetime.datetime.utcnow().isoformat(),
        'etag': etag,
        'recheck': values.get('recheck', False),
        'status': 'new'
    })

    query = _TABLE.insert().values(**values)

    flask.g.db_conn.execute(query)

    return flask.Response(json.dumps({'job': values}), 201,
                          headers={'ETag': etag},
                          content_type='application/json')


@api.route('/jobs/schedule', methods=['POST'])
@auth.requires_auth
def schedule_jobs(user):
    """Dispatch jobs to remotecis.

    The remoteci can use this method to request a new job. The server will try
    in the following order:
    - to reuse an existing job associated to the remoteci if the recheck field
      is True. In this case, the job is reinitialized has if it was a new job.
    - or to search a jobdefinition that has not been proceeded yet and create
      a fresh job associated to this jobdefinition and remoteci.
    """
    values = schemas.job_schedule.post(flask.request.json)
    topic_id = values.pop('topic_id')
    etag = utils.gen_etag()
    values.update({
        'id': utils.gen_uuid(),
        'created_at': datetime.datetime.utcnow().isoformat(),
        'updated_at': datetime.datetime.utcnow().isoformat(),
        'etag': etag,
        'recheck': values.get('recheck', False),
        'status': 'new'
    })
    rci_id = values.get('remoteci_id')
    remoteci = v1_utils.verify_existence_and_get(rci_id, models.REMOTECIS)
    v1_utils.verify_existence_and_get(topic_id, models.TOPICS)

    if remoteci['active'] is False:
        message = 'RemoteCI "%s" is not activated.' % rci_id
        raise dci_exc.DCIException(message, status_code=412)

    # First try to get some job to recheck
    where_clause = sql.expression.and_(
        _TABLE.c.recheck == True,  # noqa
        _TABLE.c.remoteci_id == rci_id
    )
    get_recheck_job_query = (sql.select([_TABLE])
                             .where(where_clause)
                             .limit(1))

    recheck_job = flask.g.db_conn.execute(get_recheck_job_query).fetchone()
    if recheck_job:
        # Reinit the pending job like if it was a new one
        query = _TABLE.update().where(_TABLE.c.id == recheck_job.id).values({
            'created_at': datetime.datetime.utcnow().isoformat(),
            'updated_at': datetime.datetime.utcnow().isoformat(),
            'etag': etag,
            'recheck': False,
            'status': 'new'
        })
        flask.g.db_conn.execute(query)
        return flask.Response(json.dumps({'job': recheck_job}), 201,
                              headers={'ETag': etag},
                              content_type='application/json')

    v1_utils.verify_team_in_topic(user, topic_id)
    # The user belongs to the topic then we can start the scheduling

    # Subquery, get all the jobdefinitions which have been run by this remoteci
    sub_query = (sql
                 .select([_TABLE.c.jobdefinition_id])
                 .where(_TABLE.c.remoteci_id == rci_id))

    # Get one jobdefinition which has not been run by this remoteci
    where_clause = sql.expression.and_(
        sql.expression.not_(
            models.JOBDEFINITIONS.c.id.in_(sub_query)),
        models.JOBDEFINITIONS.c.topic_id == topic_id,  # noqa,
        models.JOBDEFINITIONS.c.active == True,  # noqa
    )

    query = (sql.select([models.JOBDEFINITIONS.c.id])
             .where(where_clause)
             .order_by(sql.asc(models.JOBDEFINITIONS.c.priority))
             .limit(1))
    # Order by jobdefinition.priority and get the first one

    jobdefinition_to_run = flask.g.db_conn.execute(query).fetchone()

    if jobdefinition_to_run is None:
        raise dci_exc.DCIException('No jobs available for run.',
                                   status_code=412)

    values.update({
        'jobdefinition_id': jobdefinition_to_run[0],
        'team_id': remoteci['team_id']
    })

    query = _TABLE.insert().values(**values)

    flask.g.db_conn.execute(query)

    return flask.Response(json.dumps({'job': values}), 201,
                          headers={'ETag': etag},
                          content_type='application/json')


@api.route('/jobs', methods=['GET'])
@auth.requires_auth
def get_all_jobs(user, jd_id=None):
    """Get all jobs.

    If jd_id is not None, then return all the jobs with a jobdefinition
    pointed by jd_id.
    """
    # get the diverse parameters
    args = schemas.args(flask.request.args.to_dict())
    embed = args['embed']

    v1_utils.verify_embed_list(embed, _VALID_EMBED.keys())
    q_bd = v1_utils.QueryBuilder(_TABLE, args['offset'], args['limit'])

    select, join = v1_utils.get_query_with_join(embed, _VALID_EMBED)

    q_bd.select.extend(select)
    q_bd.join.extend(join)
    q_bd.sort = v1_utils.sort_query(args['sort'], _JOBS_COLUMNS)
    q_bd.where = v1_utils.where_query(args['where'], _TABLE, _JOBS_COLUMNS)

    # If it's not an admin then restrict the view to the team's file
    if not auth.is_admin(user):
        q_bd.where.append(_TABLE.c.team_id == user['team_id'])

    if jd_id is not None:
        q_bd.where.append(_TABLE.c.jobdefinition_id == jd_id)

    # get the number of rows for the '_meta' section
    nb_row = flask.g.db_conn.execute(q_bd.build_nb_row()).scalar()
    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()
    rows = [v1_utils.group_embedded_resources(embed, row) for row in rows]

    return flask.jsonify({'jobs': rows, '_meta': {'count': nb_row}})


@api.route('/jobs/<j_id>/jobstates', methods=['GET'])
@auth.requires_auth
def get_jobstates_by_job(user, j_id):
    v1_utils.verify_existence_and_get(j_id, _TABLE)
    return jobstates.get_all_jobstates(j_id=j_id)


@api.route('/jobs/<jd_id>', methods=['GET'])
@auth.requires_auth
def get_job_by_id(user, jd_id):
    # get the diverse parameters
    embed = schemas.args(flask.request.args.to_dict())['embed']
    v1_utils.verify_embed_list(embed, _VALID_EMBED.keys())

    q_bd = v1_utils.QueryBuilder(_TABLE)

    select, join = v1_utils.get_query_with_join(embed, _VALID_EMBED)
    q_bd.select.extend(select)
    q_bd.join.extend(join)

    if not auth.is_admin(user):
        q_bd.where.append(_TABLE.c.team_id == user['team_id'])

    q_bd.where.append(_TABLE.c.id == jd_id)

    row = flask.g.db_conn.execute(q_bd.build()).fetchone()
    if row is None:
        raise dci_exc.DCINotFound('Job', jd_id)

    job = v1_utils.group_embedded_resources(embed, row)
    res = flask.jsonify({'job': job})
    res.headers.add_header('ETag', job['etag'])
    return res


@api.route('/jobs/<job_id>', methods=['PUT'])
@auth.requires_auth
def update_job_by_id(user, job_id):
    """Update a job
    """
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    # get the diverse parameters
    values = schemas.job.put(flask.request.json)

    job = v1_utils.verify_existence_and_get(job_id, _TABLE)

    # If it's an admin or belongs to the same team
    if not(auth.is_admin(user) or auth.is_in_team(user, job['team_id'])):
        raise auth.UNAUTHORIZED

    # Update jobstate if needed
    status = values.get('status')
    if status and job.status != status:
        jobstates.insert_jobstate(user, {
            'status': status,
            'job_id': job_id
        })

    where_clause = sql.and_(_TABLE.c.etag == if_match_etag,
                            _TABLE.c.id == job_id)

    values['etag'] = utils.gen_etag()
    query = _TABLE.update().where(where_clause).values(**values)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict('Job', job_id)

    return flask.Response(None, 204, headers={'ETag': values['etag']},
                          content_type='application/json')


@api.route('/jobs/<j_id>/recheck', methods=['POST'])
@auth.requires_auth
def job_recheck(user, j_id):

    job_to_recheck = v1_utils.verify_existence_and_get(j_id, _TABLE)
    if not (auth.is_admin(user) or
            auth.is_in_team(user, job_to_recheck['team_id'])):
        raise auth.UNAUTHORIZED
    etag = utils.gen_etag()
    values = utils.dict_merge(dict(job_to_recheck), {
        'id': utils.gen_uuid(),
        'created_at': datetime.datetime.utcnow().isoformat(),
        'updated_at': datetime.datetime.utcnow().isoformat(),
        'etag': etag,
        'recheck': True,
        'status': 'new'
    })
    query = _TABLE.insert().values(**values)

    flask.g.db_conn.execute(query)

    return flask.Response(json.dumps({'job': values}), 201,
                          headers={'ETag': etag},
                          content_type='application/json')


@api.route('/jobs/<j_id>/files', methods=['POST'])
@auth.requires_auth
def add_file_to_jobs(user, j_id):
    values = schemas.job.post(flask.request.json)

    values.update({'job_id': j_id})

    return files.create_files(user, values)


@api.route('/jobs/<j_id>/files', methods=['GET'])
@auth.requires_auth
def get_all_files_from_jobs(user, j_id):
    """Get all files.
    """
    return files.get_all_files(j_id)


@api.route('/jobs/<j_id>', methods=['DELETE'])
@auth.requires_auth
def delete_job_by_id(user, j_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    job = v1_utils.verify_existence_and_get(j_id, _TABLE)

    if not (auth.is_admin(user) or auth.is_in_team(user, job['team_id'])):
        raise auth.UNAUTHORIZED

    where_clause = sql.and_(_TABLE.c.id == j_id,
                            _TABLE.c.etag == if_match_etag)
    query = _TABLE.delete().where(where_clause)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIDeleteConflict('Job', j_id)

    return flask.Response(None, 204, content_type='application/json')
