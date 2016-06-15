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
import six
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
    'file': v1_utils.embed(models.FILES),
    'jobdefinition': v1_utils.embed(models.JOBDEFINITIONS),
    # TODO(spredzy) : Remove this when the join and multiple
    # entities is supported
    'jobdefinition.jobdefinition_component':
        v1_utils.embed(models.JOIN_JOBDEFINITIONS_COMPONENTS),
    'jobdefinition.test': v1_utils.embed(models.TESTS),
    'team': v1_utils.embed(models.TEAMS),
    'remoteci': v1_utils.embed(models.REMOTECIS)
}


@api.route('/jobs', methods=['POST'])
@auth.requires_auth
def create_jobs(user):
    values = schemas.job.post(flask.request.json)
    components_ids = values.pop('components')

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
        'status': 'new',
        'configuration': {}
    })

    # create the job and feed the jobs_components table
    with flask.g.db_conn.begin():
        query = _TABLE.insert().values(**values)
        flask.g.db_conn.execute(query)

        jobs_components_to_insert = []
        for cmpt_id in components_ids:
            v1_utils.verify_existence_and_get(cmpt_id, models.COMPONENTS)
            jobs_components_to_insert.append({'job_id': values['id'],
                                              'component_id': cmpt_id})
        if jobs_components_to_insert:
            flask.g.db_conn.execute(models.JOIN_JOBS_COMPONENTS.insert(),
                                    jobs_components_to_insert)

    return flask.Response(json.dumps({'job': values}), 201,
                          headers={'ETag': etag},
                          content_type='application/json')


@api.route('/jobs/search', methods=['POST'])
@auth.requires_auth
def search_jobs(user):
    values = schemas.job_search.post(flask.request.json)
    jobdefinition_id = values.get('jobdefinition_id')
    configuration = values.get('configuration')
    config_op = configuration.pop('_op', 'and')

    args = schemas.args(flask.request.args.to_dict())
    q_bd = v1_utils.QueryBuilder(_TABLE, args['offset'], args['limit'])
    q_bd.sort = v1_utils.sort_query(args['sort'], _JOBS_COLUMNS)

    # If it's not an admin then restrict the view to the team's file
    if not auth.is_admin(user):
        q_bd.where.append(_TABLE.c.team_id == user['team_id'])

    if jobdefinition_id is not None:
        q_bd.where.append(_TABLE.c.jobdefinition_id == jobdefinition_id)

    if config_op == 'and':
        sa_op = sql.expression.and_
    elif config_op == 'or':
        sa_op = sql.expression.or_

    filering_rules = []
    for k, v in six.iteritems(configuration):
        path = []
        for sk in k.split('.'):
            path.append(sk)
        filering_rules.append(_TABLE.c.configuration[path].astext == v)
    q_bd.where.append(sa_op(*filering_rules))

    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()

    return flask.jsonify({'jobs': rows, '_meta': {'count': len(rows)}})


def _recheck_job(remoteci_id):
    """Return a job to recheck if one exists."""
    # First try to get some job to recheck
    where_clause = sql.expression.and_(
        _TABLE.c.recheck == True,  # noqa
        _TABLE.c.remoteci_id == remoteci_id
    )
    return sql.select([_TABLE]).where(where_clause).limit(1)


def _build_recheck(recheck_job, values):
    recheck_job = dict(recheck_job)

    # Reinit the pending as if it were new.
    values.update({'id': recheck_job['id'], 'recheck': False})
    recheck_job.update(values)

    flask.g.db_conn.execute(
        _TABLE.update()
        .where(_TABLE.c.id == recheck_job['id'])
        .values(recheck_job)
    )
    return recheck_job


def _build_new(topic_id, remoteci, values):
    JDC = models.JOIN_JOBDEFINITIONS_COMPONENTS
    JJC = models.JOIN_JOBS_COMPONENTS

    # Subquery, get all the jobdefinitions which have been run by this remoteci
    sub_query = (sql
                 .select([_TABLE.c.jobdefinition_id])
                 .where(_TABLE.c.remoteci_id == remoteci['id']))

    # Get one jobdefinition which has not been run by this remoteci
    where_clause = sql.expression.and_(
        sql.expression.not_(models.JOBDEFINITIONS.c.id.in_(sub_query)),
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
    insert_query = _TABLE.insert().values(**values)
    with flask.g.db_conn.begin():
        flask.g.db_conn.execute(insert_query)

        # for smooth migration to the new scheduler, feed jobs_component table
        query = (sql.select([models.COMPONENTS.c.id])
                 .select_from(JDC.join(models.COMPONENTS))
                 .where(JDC.c.jobdefinition_id == jobdefinition_to_run[0]))

        components_from_jd = list(flask.g.db_conn.execute(query))

        jjcs = [{'job_id': values['id'], 'component_id': cfjd[0]}
                for cfjd in components_from_jd]
        flask.g.db_conn.execute(JJC.insert(), jjcs)

    return values


def _build_new_template(topic_id, remoteci, values):
    # Get a jobdefinition
    q_jd = sql.select([models.JOBDEFINITIONS]).where(
        models.JOBDEFINITIONS.c.topic_id == topic_id).order_by(
        sql.asc(models.JOBDEFINITIONS.c.created_at))
    jd_to_run = flask.g.db_conn.execute(q_jd).fetchone()

    if jd_to_run is None:
        msg = 'Jobdefinition not found.'
        raise dci_exc.DCIException(msg, status_code=412)

    # Get the latest components according to the component_types of the
    # jobdefinition.
    component_types = tuple(jd_to_run['component_types'])
    if not component_types:
        msg = ('Jobdefinition "%s" malformed: no component types provided.' %
               jd_to_run['id'])
        raise dci_exc.DCIException(msg, status_code=412)

    # TODO(yassine): use a tricky join/group by to remove the for clause
    schedule_components_ids = []
    for ct in component_types:
        where_clause = sql.and_(models.COMPONENTS.c.type == ct,
                                models.COMPONENTS.c.topic_id == topic_id)
        query = (sql.select([models.COMPONENTS.c.id])
                 .where(where_clause)
                 .order_by(sql.asc(models.COMPONENTS.c.created_at)))
        cmpt_id = flask.g.db_conn.execute(query).fetchone()[0]

        if cmpt_id is None:
            msg = 'Component of type "%s" not found.' % ct
            raise dci_exc.DCIException(msg, status_code=412)

        if cmpt_id in schedule_components_ids:
            msg = ('Jobdefinition "%s" malformed: type "%s" duplicated.' %
                   (jd_to_run['id'], ct))
            raise dci_exc.DCIException(msg, status_code=412)
        schedule_components_ids.append(cmpt_id)

    values.update({
        'jobdefinition_id': jd_to_run['id'],
        'team_id': remoteci['team_id']
    })

    with flask.g.db_conn.begin():
        # create the job
        flask.g.db_conn.execute(_TABLE.insert().values(**values))

        # Adds the components to the jobs using join_jobs_components
        job_components = [
            {'job_id': values['id'], 'component_id': sci}
            for sci in schedule_components_ids
        ]
        flask.g.db_conn.execute(
            models.JOIN_JOBS_COMPONENTS.insert(), job_components
        )

    return values


def _validate_input(values, user):
    topic_id = values.pop('topic_id')
    remoteci_id = values.get('remoteci_id')

    values.update({
        'id': utils.gen_uuid(),
        'created_at': datetime.datetime.utcnow().isoformat(),
        'updated_at': datetime.datetime.utcnow().isoformat(),
        'etag': utils.gen_etag(),
        'recheck': values.get('recheck', False),
        'status': 'new'
    })

    remoteci = v1_utils.verify_existence_and_get(remoteci_id, models.REMOTECIS)
    v1_utils.verify_existence_and_get(topic_id, models.TOPICS)

    # let's kill existing running jobs for the remoteci
    where_clause = sql.expression.and_(
        _TABLE.c.remoteci_id == remoteci_id,
        _TABLE.c.status.in_(('new', 'pre-run', 'running', 'post-run'))
    )
    kill_query = _TABLE .update().where(where_clause).values(status='killed')
    flask.g.db_conn.execute(kill_query)

    if remoteci['active'] is False:
        message = 'RemoteCI "%s" is disabled.' % remoteci_id
        raise dci_exc.DCIException(message, status_code=412)

    # The user belongs to the topic then we can start the scheduling
    v1_utils.verify_team_in_topic(user, topic_id)
    return topic_id, remoteci


@api.route('/jobs/schedule', methods=['POST'])
@auth.requires_auth
def schedule_jobs(user):
    """Dispatch jobs to remotecis.

    The remoteci can use this method to request a new job. The server will try
    in the following order:
    - to reuse an existing job associated to the remoteci if the recheck field
      is True. In this case, the job is reinitialized as if it was a new job.
    - or to search a jobdefinition that has not been proceeded yet and create
      a fresh job associated to this jobdefinition and remoteci.
    Before a job is dispatched, the server will flag as 'killed' all the
    running jobs that were associated with the remoteci. This is because they
    will never be finished.
    """
    values = schemas.job_schedule.post(flask.request.json)

    topic_id, remoteci = _validate_input(values, user)

    # test if there is some job to recheck
    query = _recheck_job(remoteci['id'])
    recheck_job = flask.g.db_conn.execute(query).fetchone()
    if recheck_job:
        values = _build_recheck(recheck_job, values)
    else:
        values = _build_new_template(topic_id, remoteci, values)

    return flask.Response(json.dumps({'job': values}), 201,
                          headers={'ETag': values['etag']},
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

    q_bd = v1_utils.QueryBuilder(_TABLE, args['offset'], args['limit'],
                                 _VALID_EMBED)

    # Its not necessary to retrieve job configuration on job list
    q_bd.ignore_columns(['configuration'])
    q_bd.join(embed)
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


@api.route('/jobs/<job_id>/components', methods=['GET'])
@auth.requires_auth
def get_components_from_job(user, job_id):
    v1_utils.verify_existence_and_get(job_id, _TABLE)

    # Get all components which are attached to a given job
    JJC = models.JOIN_JOBS_COMPONENTS
    query = (sql.select([models.COMPONENTS])
             .select_from(JJC.join(models.COMPONENTS))
             .where(JJC.c.job_id == job_id))
    rows = flask.g.db_conn.execute(query)

    return flask.jsonify({'components': rows,
                          '_meta': {'count': rows.rowcount}})


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

    q_bd = v1_utils.QueryBuilder(_TABLE, embed=_VALID_EMBED)
    q_bd.join(embed)

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
        'status': 'new',
        'configuration': None,
    })
    query = _TABLE.insert().values(**values)
    with flask.g.db_conn.begin():
        flask.g.db_conn.execute(query)
        # feed jobs_component table
        JDC = models.JOIN_JOBS_COMPONENTS
        query = (sql.select([models.COMPONENTS.c.id])
                 .select_from(JDC.join(models.COMPONENTS))
                 .where(JDC.c.job_id == j_id))
        components_from_old_job = list(flask.g.db_conn.execute(query))
        jobs_components_to_insert = [{'job_id': values['id'],
                                      'component_id': cfjd[0]}
                                     for cfjd in components_from_old_job]
        flask.g.db_conn.execute(models.JOIN_JOBS_COMPONENTS.insert(),
                                jobs_components_to_insert)

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
