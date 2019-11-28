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
from sqlalchemy import exc as sa_exc
from sqlalchemy import sql

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import components
from dci.api.v1 import utils as v1_utils
from dci.api.v1 import jobs_events
from dci.api.v1 import tags
from dci import decorators
from dci.common import audits
from dci.common import exceptions as dci_exc
from dci.common.schemas import (
    check_json_is_valid,
    update_job_schema,
    upgrade_job_schema,
    create_job_schema,
    check_and_get_args
)
from dci.common import utils
from dci.db import embeds
from dci.db import models

from dci.api.v1 import files
from dci.api.v1 import export_control
from dci.api.v1 import issues
from dci.api.v1 import jobstates
from dci.api.v1 import remotecis
from dci import dci_config


_FILES_FOLDER = dci_config.CONFIG['FILES_UPLOAD_FOLDER']
_TABLE = models.JOBS
_VALID_EMBED = embeds.jobs()
# associate column names with the corresponding SA Column object
_JOBS_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)
_EMBED_MANY = {
    'files': True,
    'topic': False,
    'components': True,
    'topicsecondary': False,
    'componentssecondary': True,
    'issues': True,
    'jobstates': True,
    'remoteci': False,
    'team': False,
    'results': True,
    'analytics': True,
    'tags': True
}


def get_utc_now():
    return datetime.datetime.utcnow()


def _build_job(product_id, topic_id, remoteci, components_ids, values,
               topic_id_secondary=None, previous_job_id=None,
               update_previous_job_id=None):

    # get components of primary topic
    p_component_types = components.get_component_types_from_topic(topic_id)
    p_schedule_components_ids = components.get_schedule_components_ids(
        topic_id, p_component_types, components_ids)

    # get components of secondary topic
    s_schedule_components_ids = []
    if topic_id_secondary:
        s_component_types = components.get_component_types_from_topic(
            topic_id_secondary)
        s_schedule_components_ids = components.get_schedule_components_ids(
            topic_id_secondary, s_component_types, [])

    values.update({
        'product_id': product_id,
        'topic_id': topic_id,
        'topic_id_secondary': topic_id_secondary,
        'team_id': remoteci['team_id'],
        'previous_job_id': previous_job_id,
        'update_previous_job_id': update_previous_job_id
    })

    with flask.g.db_conn.begin():
        # create the job
        flask.g.db_conn.execute(_TABLE.insert().values(**values))

        if len(p_schedule_components_ids) > 0:
            # Adds the components to the jobs using join_jobs_components
            job_components = [
                {'job_id': values['id'], 'component_id': sci}
                for sci in p_schedule_components_ids
            ]

            flask.g.db_conn.execute(
                models.JOIN_JOBS_COMPONENTS.insert(), job_components
            )
        if len(s_schedule_components_ids) > 0:
            # Adds the components to the jobs using join_jobs_components
            job_components = [
                {'job_id': values['id'], 'component_id': sci}
                for sci in s_schedule_components_ids
            ]

            flask.g.db_conn.execute(
                models.JOIN_JOBS_COMPONENTS.insert(), job_components
            )

    return values


def _get_job(user, job_id, embed=None):
    # build the query thanks to the QueryBuilder class
    args = {'embed': embed}
    query = v1_utils.QueryBuilder(_TABLE, args, _JOBS_COLUMNS)

    if (user.is_not_super_admin() and user.is_not_read_only_user()
        and user.is_not_epm()):
        query.add_extra_condition(_TABLE.c.team_id.in_(user.teams_ids))

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


@api.route('/jobs', methods=['POST'])
@api.route('/jobs/schedule', methods=['POST'])
@decorators.login_required
def create_jobs(user):
    """Dispatch jobs to remotecis.

    The remoteci can use this method to request a new job.

    Before a job is dispatched, the server will flag as 'killed' all the
    running jobs that were associated with the remoteci. This is because they
    will never be finished.
    """
    values = flask.request.json
    check_json_is_valid(create_job_schema, values)

    components_ids = values.pop('components', None)

    previous_job_id = values.get('previous_job_id')
    if previous_job_id:
        v1_utils.verify_existence_and_get(previous_job_id, _TABLE)

    values.update({
        'id': utils.gen_uuid(),
        'created_at': get_utc_now().isoformat(),
        'updated_at': get_utc_now().isoformat(),
        'etag': utils.gen_etag(),
        'status': 'new',
        'remoteci_id': user.id,
        'duration': 0,
        'previous_job_id': previous_job_id,
        'team_id': user.teams_ids[0],
        'user_agent': flask.request.environ.get('HTTP_USER_AGENT'),
        'client_version': flask.request.environ.get(
            'HTTP_CLIENT_VERSION'
        ),
    })
    topic_id = values.pop('topic_id')
    dry_run = values.pop('dry_run')
    if dry_run:
        component_types = components.get_component_types_from_topic(topic_id)
        _components = components.get_last_components_by_type(
            component_types,
            topic_id
        )
        return flask.Response(
            json.dumps({'components': _components, 'job': None}),
            201,
            content_type='application/json'
        )

    # check remoteci
    remoteci = v1_utils.verify_existence_and_get(user.id, models.REMOTECIS)
    if remoteci['state'] != 'active':
        message = 'RemoteCI "%s" is disabled.' % remoteci['id']
        raise dci_exc.DCIException(message, status_code=412)

    # check primary topic
    topic = v1_utils.verify_existence_and_get(topic_id, models.TOPICS)
    product_id = topic['product_id']
    if topic['state'] != 'active':
        msg = 'Topic %s:%s not active.' % (topic_id, topic['name'])
        raise dci_exc.DCIException(msg, status_code=412)
    export_control.verify_access_to_topic(user, topic)

    # check secondary topic
    topic_id_secondary = values.pop('topic_id_secondary')
    if topic_id_secondary:
        topic_secondary = v1_utils.verify_existence_and_get(
            topic_id_secondary, models.TOPICS)
        if topic_secondary['state'] != 'active':
            msg = 'Topic %s:%s not active.' % (topic_id_secondary,
                                               topic['name'])
            raise dci_exc.DCIException(msg, status_code=412)
        export_control.verify_access_to_topic(user, topic_secondary)

    remotecis.kill_existing_jobs(remoteci['id'])

    components_ids = values.pop('components_ids')
    values = _build_job(product_id, topic_id, remoteci, components_ids, values,
                        previous_job_id=previous_job_id,
                        topic_id_secondary=topic_id_secondary)

    return flask.Response(json.dumps({'job': values}), 201,
                          headers={'ETag': values['etag']},
                          content_type='application/json')


@api.route('/jobs/<uuid:job_id>/update', methods=['POST'])
@decorators.login_required
def create_new_update_job_from_an_existing_job(user, job_id):
    """Create a new job in the same topic as the job_id provided and
    associate the latest components of this topic."""

    values = {
        'id': utils.gen_uuid(),
        'created_at': get_utc_now().isoformat(),
        'updated_at': get_utc_now().isoformat(),
        'etag': utils.gen_etag(),
        'status': 'new'
    }

    original_job_id = job_id
    original_job = v1_utils.verify_existence_and_get(original_job_id,
                                                     models.JOBS)

    if user.is_not_in_team(original_job['team_id']) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    # get the remoteci
    remoteci_id = str(original_job['remoteci_id'])
    remoteci = v1_utils.verify_existence_and_get(remoteci_id,
                                                 models.REMOTECIS)
    values.update({'remoteci_id': remoteci_id})

    # get the associated topic
    topic_id = str(original_job['topic_id'])
    topic = v1_utils.verify_existence_and_get(topic_id, models.TOPICS)
    product_id = topic['product_id']
    v1_utils.verify_existence_and_get(topic_id, models.TOPICS)

    values.update({
        'user_agent': flask.request.environ.get('HTTP_USER_AGENT'),
        'client_version': flask.request.environ.get(
            'HTTP_CLIENT_VERSION'
        ),
    })

    values = _build_job(product_id, topic_id, remoteci, [], values,
                        update_previous_job_id=original_job_id)

    return flask.Response(json.dumps({'job': values}), 201,
                          headers={'ETag': values['etag']},
                          content_type='application/json')


@api.route('/jobs/upgrade', methods=['POST'])
@decorators.login_required
def create_new_upgrade_job_from_an_existing_job(user):
    """Create a new job in the 'next topic' of the topic of
    the provided job_id."""
    values = flask.request.json
    check_json_is_valid(upgrade_job_schema, values)

    values.update({
        'id': utils.gen_uuid(),
        'created_at': get_utc_now().isoformat(),
        'updated_at': get_utc_now().isoformat(),
        'etag': utils.gen_etag(),
        'status': 'new'
    })

    original_job_id = values.pop('job_id')
    original_job = v1_utils.verify_existence_and_get(original_job_id,
                                                     models.JOBS)
    if user.is_not_in_team(original_job['team_id']) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    # get the remoteci
    remoteci_id = str(original_job['remoteci_id'])
    remoteci = v1_utils.verify_existence_and_get(remoteci_id,
                                                 models.REMOTECIS)
    values.update({'remoteci_id': remoteci_id})

    # get the associated topic
    topic_id = str(original_job['topic_id'])
    topic = v1_utils.verify_existence_and_get(topic_id, models.TOPICS)

    values.update({
        'user_agent': flask.request.environ.get('HTTP_USER_AGENT'),
        'client_version': flask.request.environ.get(
            'HTTP_CLIENT_VERSION'
        ),
    })

    next_topic_id = topic['next_topic_id']

    if not next_topic_id:
        raise dci_exc.DCIException(
            "topic %s does not contains a next topic" % topic_id)
    topic = v1_utils.verify_existence_and_get(next_topic_id, models.TOPICS)
    product_id = topic['product_id']

    # instantiate a new job in the next_topic_id
    # todo(yassine): make possible the upgrade to choose specific components
    values = _build_job(product_id, next_topic_id, remoteci, [], values,
                        previous_job_id=original_job_id)

    return flask.Response(json.dumps({'job': values}), 201,
                          headers={'ETag': values['etag']},
                          content_type='application/json')


@api.route('/jobs', methods=['GET'])
@decorators.login_required
def get_all_jobs(user, topic_id=None):
    """Get all jobs.

    If topic_id is not None, then return all the jobs with a topic
    pointed by topic_id.
    """
    # get the diverse parameters
    args = check_and_get_args(flask.request.args.to_dict())

    # build the query thanks to the QueryBuilder class
    query = v1_utils.QueryBuilder(_TABLE, args, _JOBS_COLUMNS)

    # add extra conditions for filtering

    # # If not admin nor rh employee then restrict the view to the team
    if (user.is_not_super_admin() and user.is_not_read_only_user() and
        user.is_not_epm()):
        query.add_extra_condition(_TABLE.c.team_id.in_(user.teams_ids))

    # # If topic_id not None, then filter by topic_id
    if topic_id is not None:
        query.add_extra_condition(_TABLE.c.topic_id == topic_id)

    # # Get only the non archived jobs
    query.add_extra_condition(_TABLE.c.state != 'archived')

    nb_rows = query.get_number_of_rows()
    rows = query.execute(fetchall=True)
    rows = v1_utils.format_result(rows, _TABLE.name, args['embed'],
                                  _EMBED_MANY)

    return flask.jsonify({'jobs': rows, '_meta': {'count': nb_rows}})


@api.route('/jobs/<uuid:job_id>/components', methods=['GET'])
@decorators.login_required
def get_components_from_job(user, job_id):
    job, nb_rows = _get_job(user, job_id, ['components'])
    return flask.jsonify({'components': job['components'],
                          '_meta': {'count': nb_rows}})


@api.route('/jobs/<uuid:job_id>/jobstates', methods=['GET'])
@decorators.login_required
def get_jobstates_by_job(user, job_id):
    v1_utils.verify_existence_and_get(job_id, _TABLE)
    return jobstates.get_all_jobstates(user, job_id)


@api.route('/jobs/<uuid:job_id>', methods=['GET'])
@decorators.login_required
def get_job_by_id(user, job_id):
    job = v1_utils.verify_existence_and_get(job_id, _TABLE)
    job_dict = dict(job)
    job_dict['issues'] = json.loads(
        issues.get_issues_by_resource(job_id, _TABLE).response[0]
    )['issues']
    return base.get_resource_by_id(user, job_dict, _TABLE, _EMBED_MANY)


@api.route('/jobs/<uuid:job_id>', methods=['PUT'])
@decorators.login_required
@audits.log
def update_job_by_id(user, job_id):
    """Update a job
    """
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    values = flask.request.json
    check_json_is_valid(update_job_schema, values)

    job = v1_utils.verify_existence_and_get(job_id, _TABLE)
    job = dict(job)

    if user.is_not_in_team(job['team_id']) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    # Update jobstate if needed
    status = values.get('status')
    if status and job.get('status') != status:
        jobstates.insert_jobstate(user, {
            'status': status,
            'job_id': job_id
        })
        if status in models.FINAL_STATUSES:
            jobs_events.create_event(job_id, status, job['topic_id'])

    where_clause = sql.and_(_TABLE.c.etag == if_match_etag,
                            _TABLE.c.id == job_id)

    values['etag'] = utils.gen_etag()
    query = _TABLE.update().returning(*_TABLE.columns).\
        where(where_clause).values(**values)

    result = flask.g.db_conn.execute(query)
    if not result.rowcount:
        raise dci_exc.DCIConflict('Job', job_id)

    return flask.Response(
        json.dumps({'job': result.fetchone()}), 200,
        headers={'ETag': values['etag']},
        content_type='application/json'
    )


@api.route('/jobs/<uuid:j_id>/files', methods=['POST'])
@decorators.login_required
def add_file_to_jobs(user, j_id):
    values = flask.request.json
    check_json_is_valid(create_job_schema, values)
    values.update({'job_id': j_id})

    return files.create_files(user, values)


@api.route('/jobs/<uuid:j_id>/issues', methods=['GET'])
@decorators.login_required
def retrieve_issues_from_job(user, j_id):
    """Retrieve all issues attached to a job."""
    return issues.get_issues_by_resource(j_id, _TABLE)


@api.route('/jobs/<uuid:j_id>/issues', methods=['POST'])
@decorators.login_required
def attach_issue_to_jobs(user, j_id):
    """Attach an issue to a job."""
    return issues.attach_issue(j_id, _TABLE, user.id)


@api.route('/jobs/<uuid:j_id>/issues/<uuid:i_id>', methods=['DELETE'])
@decorators.login_required
def unattach_issue_from_job(user, j_id, i_id):
    """Unattach an issue to a job."""
    return issues.unattach_issue(j_id, i_id, _TABLE)


@api.route('/jobs/<uuid:j_id>/files', methods=['GET'])
@decorators.login_required
def get_all_files_from_jobs(user, j_id):
    """Get all files.
    """
    return files.get_all_files(user, j_id)


@api.route('/jobs/<uuid:j_id>/results', methods=['GET'])
@decorators.login_required
def get_all_results_from_jobs(user, j_id):
    """Get all results from job.
    """

    job = v1_utils.verify_existence_and_get(j_id, _TABLE)

    if (user.is_not_in_team(job['team_id']) and user.is_not_read_only_user()
        and user.is_not_epm()):
        raise dci_exc.Unauthorized()

    # get testscases from tests_results
    query = sql.select([models.TESTS_RESULTS]). \
        where(models.TESTS_RESULTS.c.job_id == job['id'])
    all_tests_results = flask.g.db_conn.execute(query).fetchall()

    results = []
    for test_result in all_tests_results:
        test_result = dict(test_result)
        results.append({'filename': test_result['name'],
                        'name': test_result['name'],
                        'total': test_result['total'],
                        'failures': test_result['failures'],
                        'errors': test_result['errors'],
                        'skips': test_result['skips'],
                        'time': test_result['time'],
                        'regressions': test_result['regressions'],
                        'successfixes': test_result['successfixes'],
                        'success': test_result['success'],
                        'file_id': test_result['file_id']})

    return flask.jsonify({'results': results,
                          '_meta': {'count': len(results)}})


@api.route('/jobs/<uuid:j_id>', methods=['DELETE'])
@decorators.login_required
def delete_job_by_id(user, j_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    job = v1_utils.verify_existence_and_get(j_id, _TABLE)

    if ((user.is_not_in_team(job['team_id']) or user.is_read_only_user()) and
        user.is_not_epm()):
        raise dci_exc.Unauthorized()

    with flask.g.db_conn.begin():
        values = {'state': 'archived'}
        where_clause = sql.and_(_TABLE.c.id == j_id,
                                _TABLE.c.etag == if_match_etag)
        query = _TABLE.update().where(where_clause).values(**values)

        result = flask.g.db_conn.execute(query)

        if not result.rowcount:
            raise dci_exc.DCIDeleteConflict('Job', j_id)

        for model in [models.FILES]:
            query = model.update().where(model.c.job_id == j_id).values(
                **values
            )
            flask.g.db_conn.execute(query)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/jobs/<uuid:job_id>/tags', methods=['GET'])
@decorators.login_required
def get_tags_from_job(user, job_id):
    """Retrieve all tags attached to a job."""

    job = v1_utils.verify_existence_and_get(job_id, _TABLE)
    if (user.is_not_in_team(job['team_id']) and user.is_not_read_only_user()
        and user.is_not_epm()):
        raise dci_exc.Unauthorized()

    JTT = models.JOIN_JOBS_TAGS
    query = (sql.select([models.TAGS])
             .select_from(JTT.join(models.TAGS))
             .where(JTT.c.job_id == job_id))
    rows = flask.g.db_conn.execute(query)

    return flask.jsonify({'tags': rows, '_meta': {'count': rows.rowcount}})


@api.route('/jobs/<uuid:job_id>/tags', methods=['POST'])
@decorators.login_required
def add_tag_to_job(user, job_id):
    """Add a tag to a job."""

    job = v1_utils.verify_existence_and_get(job_id, _TABLE)
    if user.is_not_in_team(job['team_id']) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    values = {
        'job_id': job_id
    }

    with flask.g.db_conn.begin():
        job_tagged = tags.add_tag_to_resource(values, models.JOIN_JOBS_TAGS)
        # update the job tag field
        job_values = {}
        job_values['etag'] = utils.gen_etag()
        tag_name = flask.request.json.get('name')
        tag_name = [tag_name] if tag_name else []
        job_values['tag'] = job['tag'] + tag_name
        query = _TABLE.update().where(_TABLE.c.id == job_id).values(**job_values)

        result = flask.g.db_conn.execute(query)
        if not result.rowcount:
            raise dci_exc.DCIConflict('Job', job_id)

    return flask.Response(json.dumps(job_tagged), 201,
                          content_type='application/json')


@api.route('/jobs/<uuid:job_id>/tags/<uuid:tag_id>', methods=['DELETE'])
@decorators.login_required
def delete_tag_from_job(user, job_id, tag_id):
    """Delete a tag from a job."""

    _JJT = models.JOIN_JOBS_TAGS
    job = v1_utils.verify_existence_and_get(job_id, _TABLE)
    if user.is_not_in_team(job['team_id']) and user.is_not_epm():
        raise dci_exc.Unauthorized()
    tag = v1_utils.verify_existence_and_get(tag_id, models.TAGS)
    tag_name = tag['name']

    with flask.g.db_conn.begin():
        query = _JJT.delete().where(sql.and_(_JJT.c.tag_id == tag_id,
                                             _JJT.c.job_id == job_id))
        try:
            flask.g.db_conn.execute(query)
        except sa_exc.IntegrityError:
            raise dci_exc.DCICreationConflict('tag', 'tag_id')
            # update the job tag field
        job_values = {}
        job_values['etag'] = utils.gen_etag()
        tag_name = [tag_name] if tag_name else []
        job_values['tag'] = list(set(job['tag']) - set(tag_name))
        query = _TABLE.update().where(_TABLE.c.id == job_id).values(**job_values)

        result = flask.g.db_conn.execute(query)
        if not result.rowcount:
            raise dci_exc.DCIConflict('Job', job_id)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/jobs/purge', methods=['GET'])
@decorators.login_required
def get_to_purge_archived_jobs(user):
    return base.get_to_purge_archived_resources(user, _TABLE)


@api.route('/jobs/purge', methods=['POST'])
@decorators.login_required
def purge_archived_jobs(user):
    files.purge_archived_files()
    return base.purge_archived_resources(user, _TABLE)
