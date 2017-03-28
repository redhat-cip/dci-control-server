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
from dci.api.v1 import base
from dci.api.v1 import transformations as tsfm
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci.common import audits
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import embeds
from dci.db import models

from dci.api.v1 import files
from dci.api.v1 import issues
from dci.api.v1 import jobstates
from dci.api.v1 import metas
from dci import dci_config


_FILES_FOLDER = dci_config.generate_conf()['FILES_UPLOAD_FOLDER']
_TABLE = models.JOBS
_VALID_EMBED = embeds.jobs()
# associate column names with the corresponding SA Column object
_JOBS_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)
_EMBED_MANY = {
    'files': True,
    'metas': True,
    'jobdefinition': False,
    'jobdefinition.tests': True,
    'remoteci': False,
    'remoteci.tests': True,
    'components': True,
    'team': False}


@api.route('/jobs', methods=['POST'])
@auth.requires_auth
def create_jobs(user):
    created_at, updated_at = utils.get_dates(user)
    values = schemas.job.post(flask.request.json)
    components_ids = values.pop('components')

    # If it's not a super admin nor belongs to the same team_id
    if not(auth.is_admin(user) or auth.is_in_team(user, values['team_id'])):
        raise auth.UNAUTHORIZED

    etag = utils.gen_etag()
    values.update({
        'id': utils.gen_uuid(),
        'created_at': created_at,
        'updated_at': updated_at,
        'etag': etag,
        'recheck': values.get('recheck', False),
        'status': 'new',
        'configuration': {},
        'user_agent': flask.request.environ.get('HTTP_USER_AGENT'),
        'client_version': flask.request.environ.get(
            'HTTP_CLIENT_VERSION'
        ),
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
    query = v1_utils.QueryBuilder2(_TABLE, args, _JOBS_COLUMNS,
                                   ['configuration'])

    # If it's not an admin then restrict the view to the team's file
    if not auth.is_admin(user):
        query.add_extra_condition(_TABLE.c.team_id == user['team_id'])

    if jobdefinition_id is not None:
        query.add_extra_condition(_TABLE.c.jobdefinition_id == jobdefinition_id)  # noqa

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
    query.add_extra_condition(sa_op(*filering_rules))

    nb_rows = query.get_number_of_rows()
    rows = query.execute(fetchall=True)
    rows = v1_utils.format_result(rows, _TABLE.name, args['embed'],
                                  _EMBED_MANY)

    return flask.jsonify({'jobs': rows, '_meta': {'count': nb_rows}})


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


def _build_new_template(topic_id, remoteci, values, previous_job_id=None):
    # Get a jobdefinition
    q_jd = sql.select([models.JOBDEFINITIONS]).where(
        models.JOBDEFINITIONS.c.topic_id == topic_id).order_by(
        sql.desc(models.JOBDEFINITIONS.c.created_at))
    jd_to_run = flask.g.db_conn.execute(q_jd).fetchone()

    if jd_to_run is None:
        msg = 'No jobdefinition found in topic %s.' % topic_id
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
                                models.COMPONENTS.c.topic_id == topic_id,
                                models.COMPONENTS.c.export_control == True,
                                models.COMPONENTS.c.state == 'active')  # noqa
        query = (sql.select([models.COMPONENTS.c.id])
                 .where(where_clause)
                 .order_by(sql.desc(models.COMPONENTS.c.created_at)))
        cmpt_id = flask.g.db_conn.execute(query).fetchone()

        if cmpt_id is None:
            msg = 'Component of type "%s" not found or not exported.' % ct
            raise dci_exc.DCIException(msg, status_code=412)

        cmpt_id = cmpt_id[0]
        if cmpt_id in schedule_components_ids:
            msg = ('Jobdefinition "%s" malformed: type "%s" duplicated.' %
                   (jd_to_run['id'], ct))
            raise dci_exc.DCIException(msg, status_code=412)
        schedule_components_ids.append(cmpt_id)

    values.update({
        'jobdefinition_id': jd_to_run['id'],
        'team_id': remoteci['team_id'],
        'previous_job_id': previous_job_id
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

    if remoteci['state'] != 'active':
        message = 'RemoteCI "%s" is disabled.' % remoteci_id
        raise dci_exc.DCIException(message, status_code=412)

    # The user belongs to the topic then we can start the scheduling
    v1_utils.verify_team_in_topic(user, topic_id)
    return topic_id, remoteci


def _get_job(user, job_id, embed):
    # build the query thanks to the QueryBuilder class
    args = {'embed': embed}
    query = v1_utils.QueryBuilder2(_TABLE, args, _JOBS_COLUMNS)

    if not auth.is_admin(user):
        query.add_extra_condition(_TABLE.c.team_id == user['team_id'])

    query.add_extra_condition(_TABLE.c.id == job_id)
    query.add_extra_condition(_TABLE.c.state != 'archived')

    nb_rows = query.get_number_of_rows()
    rows = query.execute(fetchall=True)
    rows = v1_utils.format_result(rows, _TABLE.name, args['embed'],
                                  _EMBED_MANY)
    if len(rows) != 1:
        raise dci_exc.DCINotFound('Job', job_id)
    job = rows[0]
    return job, nb_rows


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

    values.update({
        'user_agent': flask.request.environ.get('HTTP_USER_AGENT'),
        'client_version': flask.request.environ.get(
            'HTTP_CLIENT_VERSION'
        ),
    })
    topic_id, remoteci = _validate_input(values, user)

    # test if there is some job to recheck
    query = _recheck_job(remoteci['id'])
    recheck_job = flask.g.db_conn.execute(query).fetchone()
    if recheck_job:
        values = _build_recheck(recheck_job, values)
    else:
        values = _build_new_template(topic_id, remoteci, values)

    # add upgrade flag to the job result
    values.update({'allow_upgrade_job': remoteci['allow_upgrade_job']})

    return flask.Response(json.dumps({'job': values}), 201,
                          headers={'ETag': values['etag']},
                          content_type='application/json')


@api.route('/jobs/upgrade', methods=['POST'])
@auth.requires_auth
def upgrade_jobs(user):
    values = schemas.job_upgrade.post(flask.request.json)

    values.update({
        'id': utils.gen_uuid(),
        'created_at': datetime.datetime.utcnow().isoformat(),
        'updated_at': datetime.datetime.utcnow().isoformat(),
        'etag': utils.gen_etag(),
        'recheck': False,
        'status': 'new'
    })

    original_job_id = values.pop('job_id')
    original_job = v1_utils.verify_existence_and_get(original_job_id,
                                                     models.JOBS)
    v1_utils.verify_user_in_team(user, original_job['team_id'])

    # get the remoteci
    remoteci_id = str(original_job['remoteci_id'])
    remoteci = v1_utils.verify_existence_and_get(remoteci_id,
                                                 models.REMOTECIS)
    values.update({'remoteci_id': remoteci_id})

    # get the jobdefinition
    jobdefinition_id = str(original_job['jobdefinition_id'])
    jobdefinition = v1_utils.verify_existence_and_get(jobdefinition_id,
                                                      models.JOBDEFINITIONS)

    # get the associated topic
    topic_id = str(jobdefinition['topic_id'])
    topic = v1_utils.verify_existence_and_get(topic_id, models.TOPICS)

    values.update({
        'user_agent': flask.request.environ.get('HTTP_USER_AGENT'),
        'client_version': flask.request.environ.get(
            'HTTP_CLIENT_VERSION'
        ),
    })

    next_topic_id = topic['next_topic']

    if not next_topic_id:
        raise dci_exc.DCIException(
            "topic %s does not contains a next topic" % topic_id)

    # instantiate a new job in the next_topic_id
    values = _build_new_template(next_topic_id, remoteci, values,
                                 previous_job_id=original_job_id)

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

    # build the query thanks to the QueryBuilder class
    query = v1_utils.QueryBuilder2(_TABLE, args, _JOBS_COLUMNS,
                                   ['configuration'])

    # add extra conditions for filtering

    # # If not admin then restrict the view to the team
    if not auth.is_admin(user):
        query.add_extra_condition(_TABLE.c.team_id == user['team_id'])

    # # If jd_id not None, then filter by jobdefinition_id
    if jd_id is not None:
        query.add_extra_condition(_TABLE.c.jobdefinition_id == jd_id)

    # # Get only the non archived jobs
    query.add_extra_condition(_TABLE.c.state != 'archived')

    nb_rows = query.get_number_of_rows()
    rows = query.execute(fetchall=True)
    rows = v1_utils.format_result(rows, _TABLE.name, args['embed'],
                                  _EMBED_MANY)

    return flask.jsonify({'jobs': rows, '_meta': {'count': nb_rows}})


@api.route('/jobs/<uuid:job_id>/components', methods=['GET'])
@auth.requires_auth
def get_components_from_job(user, job_id):
    job, nb_rows = _get_job(user, job_id, ['components'])
    return flask.jsonify({'components': job['components'],
                          '_meta': {'count': nb_rows}})


@api.route('/jobs/<uuid:j_id>/jobstates', methods=['GET'])
@auth.requires_auth
def get_jobstates_by_job(user, j_id):
    v1_utils.verify_existence_and_get(j_id, _TABLE)
    return jobstates.get_all_jobstates(j_id=j_id)


@api.route('/jobs/<uuid:job_id>', methods=['GET'])
@auth.requires_auth
def get_job_by_id(user, job_id):
    # get the diverse parameters
    embed = schemas.args(flask.request.args.to_dict())['embed']
    job, _ = _get_job(user, job_id, embed)
    job['issues'] = (
        json.loads(issues.get_all_issues(job_id).response[0])['issues']
    )
    res = flask.jsonify({'job': job})
    res.headers.add_header('ETag', job['etag'])
    return res


@api.route('/jobs/<uuid:job_id>', methods=['PUT'])
@auth.requires_auth
@audits.log
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
    if values.get('status') == "failure":
        _TEAMS = models.TEAMS
        where_clause = sql.expression.and_(
            _TEAMS.c.id == job['team_id']
        )
        query = (sql.select([_TEAMS]).where(where_clause))
        team_info = flask.g.db_conn.execute(query).fetchone()
        if team_info['notification'] is True:
            if team_info['email'] is not None:
                msg = {'event': 'notification',
                       'email': team_info['email'],
                       'job_id': str(job['id'])}
                flask.g.sender.send_json(msg)
    return flask.Response(None, 204, headers={'ETag': values['etag']},
                          content_type='application/json')


@api.route('/jobs/<uuid:j_id>/recheck', methods=['POST'])
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


@api.route('/jobs/<uuid:j_id>/files', methods=['POST'])
@auth.requires_auth
def add_file_to_jobs(user, j_id):
    values = schemas.job.post(flask.request.json)

    values.update({'job_id': j_id})

    return files.create_files(user, values)


@api.route('/jobs/<uuid:j_id>/issues', methods=['GET'])
@auth.requires_auth
def retrieve_issues_from_job(user, j_id):
    """Retrieve all issues attached to a job."""
    return issues.get_all_issues(j_id)


@api.route('/jobs/<uuid:j_id>/issues', methods=['POST'])
@auth.requires_auth
def attach_issue_to_jobs(user, j_id):
    """Attach an issue to a job."""
    return issues.attach_issue(j_id)


@api.route('/jobs/<uuid:j_id>/issues/<uuid:i_id>', methods=['DELETE'])
@auth.requires_auth
def unattach_issue_from_job(user, j_id, i_id):
    """Unattach an issue to a job."""
    return issues.unattach_issue(j_id, i_id)


@api.route('/jobs/<uuid:j_id>/files', methods=['GET'])
@auth.requires_auth
def get_all_files_from_jobs(user, j_id):
    """Get all files.
    """
    return files.get_all_files(j_id)


@api.route('/jobs/<uuid:j_id>/results', methods=['GET'])
@auth.requires_auth
def get_all_results_from_jobs(user, j_id):
    """Get all results from job.
    """

    job_files = json.loads(files.get_all_files(j_id).response[0])['files']
    r_files = [file for file in job_files
               if file['mime'] == 'application/junit']

    results = []
    for file in r_files:
        file_path = v1_utils.build_file_path(_FILES_FOLDER, file['team_id'],
                                             file['id'], create=False)
        data = ''.join([s for s in utils.read(file_path, mode='r')])
        data = json.loads(tsfm.junit2json(data))

        if not isinstance(data['skips'], int):
            data['skips'] = 0

        success = (int(data['total']) - int(data['failures']) -
                   int(data['errors']) - int(data['skips']))
        results.append({'filename': file['name'],
                        'name': data['name'],
                        'total': data['total'],
                        'failures': data['failures'],
                        'errors': data['errors'],
                        'skips': data['skips'],
                        'time': data['time'],
                        'success': success})

    return flask.jsonify({'results': results,
                          '_meta': {'count': len(results)}})


@api.route('/jobs/<uuid:j_id>', methods=['DELETE'])
@auth.requires_auth
def delete_job_by_id(user, j_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    job = v1_utils.verify_existence_and_get(j_id, _TABLE)

    if not (auth.is_admin(user) or auth.is_in_team(user, job['team_id'])):
        raise auth.UNAUTHORIZED

    values = {'state': 'archived'}
    where_clause = sql.and_(_TABLE.c.id == j_id,
                            _TABLE.c.etag == if_match_etag)
    query = _TABLE.update().where(where_clause).values(**values)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIDeleteConflict('Job', j_id)

    return flask.Response(None, 204, content_type='application/json')


# jobs metas controllers

@api.route('/jobs/<uuid:j_id>/metas', methods=['POST'])
@auth.requires_auth
def associate_meta(user, j_id):
    job = v1_utils.verify_existence_and_get(j_id, _TABLE)
    if not (auth.is_admin(user) or auth.is_in_team(user, job['team_id'])):
        raise auth.UNAUTHORIZED
    return metas.create_meta(user, j_id)


@api.route('/jobs/<uuid:j_id>/metas/<uuid:m_id>', methods=['GET'])
@auth.requires_auth
def get_meta_by_id(user, j_id, m_id):
    job = v1_utils.verify_existence_and_get(j_id, _TABLE)
    if not (auth.is_admin(user) or auth.is_in_team(user, job['team_id'])):
        raise auth.UNAUTHORIZED
    return metas.get_meta_by_id(m_id)


@api.route('/jobs/<uuid:j_id>/metas', methods=['GET'])
@auth.requires_auth
def get_all_metas(user, j_id):
    job = v1_utils.verify_existence_and_get(j_id, _TABLE)
    if not (auth.is_admin(user) or auth.is_in_team(user, job['team_id'])):
        raise auth.UNAUTHORIZED
    return metas.get_all_metas_from_job(j_id)


@api.route('/jobs/<uuid:j_id>/metas/<uuid:m_id>', methods=['PUT'])
@auth.requires_auth
def put_meta(user, j_id, m_id):
    job = v1_utils.verify_existence_and_get(j_id, _TABLE)
    if not (auth.is_admin(user) or auth.is_in_team(user, job['team_id'])):
        raise auth.UNAUTHORIZED
    return metas.put_meta(j_id, m_id)


@api.route('/jobs/<uuid:j_id>/metas/<uuid:m_id>', methods=['DELETE'])
@auth.requires_auth
def delete_meta(user, j_id, m_id):
    job = v1_utils.verify_existence_and_get(j_id, _TABLE)
    if not (auth.is_admin(user) or auth.is_in_team(user, job['team_id'])):
        raise auth.UNAUTHORIZED
    return metas.delete_meta(j_id, m_id)


@api.route('/jobs/purge', methods=['GET'])
@auth.requires_auth
@auth.requires_platform_admin
def get_to_purge_archived_jobs(user):
    return base.get_to_purge_archived_resources(user, _TABLE)


@api.route('/jobs/purge', methods=['POST'])
@auth.requires_auth
@auth.requires_platform_admin
def purge_archived_jobs(user):
    return base.purge_archived_resources(user, _TABLE)
