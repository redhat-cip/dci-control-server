# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2017 Red Hat, Inc
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
from sqlalchemy import exc as sa_exc
from sqlalchemy import sql, func

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import components
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import embeds
from dci.db import models

# associate column names with the corresponding SA Column object
_TABLE = models.TOPICS
_VALID_EMBED = embeds.topics()
_T_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)
_EMBED_MANY = {
    'teams': True,
    'product': False,
    'nexttopic': False,
}


@api.route('/topics', methods=['POST'])
@decorators.login_required
@decorators.check_roles
def create_topics(user):
    values = v1_utils.common_values_dict(user)
    values.update(schemas.topic.post(flask.request.json))

    if not values['product_id']:
        values['product_id'] = user.product_id

    if not user.is_super_admin() and \
       not user.product_id == values['product_id']:
        raise auth.UNAUTHORIZED

    # todo(yassine): enabled when client updated.
    # if values['component_types'] == []:
    #     raise dci_exc.DCIException('component_types should not be void')

    query = _TABLE.insert().values(**values)

    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(_TABLE.name, 'name')

    result = json.dumps({'topic': values})
    return flask.Response(result, 201, headers={'ETag': values['etag']},
                          content_type='application/json')


@api.route('/topics/<uuid:topic_id>', methods=['GET'])
@decorators.login_required
@decorators.check_roles
def get_topic_by_id(user, topic_id):
    args = schemas.args(flask.request.args.to_dict())
    topic = v1_utils.verify_existence_and_get(topic_id, _TABLE)

    if not user.is_super_admin() and not user.is_product_owner():
        if not user.is_read_only_user():
            v1_utils.verify_team_in_topic(user, topic_id)
        if 'teams' in args['embed']:
            raise dci_exc.DCIException('embed=teams not authorized.',
                                       status_code=401)

    if (not user.is_super_admin() and
        user.product_id != topic['product_id'] and
        not user.is_read_only_user()):
            raise auth.UNAUTHORIZED

    return base.get_resource_by_id(user, topic, _TABLE, _EMBED_MANY)


@api.route('/topics', methods=['GET'])
@decorators.login_required
@decorators.check_roles
def get_all_topics(user):
    args = schemas.args(flask.request.args.to_dict())
    # if the user is an admin then he can get all the topics
    query = v1_utils.QueryBuilder(_TABLE, args, _T_COLUMNS)

    if not user.is_super_admin() and not user.is_product_owner():
        if 'teams' in args['embed']:
            raise dci_exc.DCIException('embed=teams not authorized.',
                                       status_code=401)
        if not user.is_read_only_user():
            query.add_extra_condition(_TABLE.c.id.in_(v1_utils.user_topic_ids(user)))  # noqa

    if user.is_product_owner():
        query.add_extra_condition(_TABLE.c.product_id == user.product_id)

    query.add_extra_condition(_TABLE.c.state != 'archived')

    # get the number of rows for the '_meta' section
    nb_rows = query.get_number_of_rows()
    rows = query.execute(fetchall=True)
    rows = v1_utils.format_result(rows, _TABLE.name, args['embed'],
                                  _EMBED_MANY)

    return flask.jsonify({'topics': rows, '_meta': {'count': nb_rows}})


@api.route('/topics/<uuid:topic_id>', methods=['PUT'])
@decorators.login_required
@decorators.check_roles
def put_topic(user, topic_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    values = schemas.topic.put(flask.request.json)
    topic = v1_utils.verify_existence_and_get(topic_id, _TABLE)

    if not user.is_super_admin() and \
       not user.product_id == topic['product_id']:
        raise auth.UNAUTHORIZED

    n_topic = None
    if 'next_topic' in values and values['next_topic']:
        n_topic = v1_utils.verify_existence_and_get(values['next_topic'],
                                                    _TABLE)

    if user.is_product_owner() and \
       (user.product_id != topic['product_id'] or
       (n_topic and user.product_id != n_topic['product_id'])):
            raise auth.UNAUTHORIZED

    values['etag'] = utils.gen_etag()
    where_clause = sql.and_(
        _TABLE.c.etag == if_match_etag,
        _TABLE.c.id == topic_id
    )
    query = _TABLE.update().where(where_clause).values(**values)

    result = flask.g.db_conn.execute(query)
    if not result.rowcount:
        raise dci_exc.DCIConflict('Topic', topic_id)

    return flask.Response(None, 204, headers={'ETag': values['etag']},
                          content_type='application/json')


@api.route('/topics/<uuid:topic_id>', methods=['DELETE'])
@decorators.login_required
@decorators.check_roles
def delete_topic_by_id(user, topic_id):
    topic = v1_utils.verify_existence_and_get(topic_id, _TABLE)
    if not user.is_super_admin() and \
       not user.product_id == topic['product_id']:
        raise auth.UNAUTHORIZED

    topic_id = v1_utils.verify_existence_and_get(topic_id, _TABLE, get_id=True)

    with flask.g.db_conn.begin():
        values = {'state': 'archived'}
        where_clause = sql.and_(_TABLE.c.id == topic_id)
        query = _TABLE.update().where(where_clause).values(**values)

        result = flask.g.db_conn.execute(query)

        if not result.rowcount:
            raise dci_exc.DCIDeleteConflict('Topic', topic_id)

        query = models.COMPONENTS.update().where(
            models.COMPONENTS.c.topic_id == topic_id).values(**values)
        flask.g.db_conn.execute(query)

    return flask.Response(None, 204, content_type='application/json')


# components, tests GET
@api.route('/topics/<uuid:topic_id>/components', methods=['GET'])
@decorators.login_required
@decorators.check_roles
def get_all_components(user, topic_id):
    topic_id = v1_utils.verify_existence_and_get(topic_id, _TABLE, get_id=True)
    if not user.is_read_only_user():
        v1_utils.verify_team_in_topic(user, topic_id)
    return components.get_all_components(user, topic_id=topic_id)


@api.route('/topics/<uuid:topic_id>/components/latest', methods=['GET'])
@decorators.login_required
@decorators.check_roles
def get_latest_component_per_topic(user, topic_id):
    topic_id = v1_utils.verify_existence_and_get(topic_id, _TABLE, get_id=True)
    v1_utils.verify_team_in_topic(user, topic_id)

    latest_components = components._get_latest_components()
    for component in latest_components:
        if component['topic_id'] == topic_id:
            last_component = component
            break

    return flask.jsonify({'component': last_component})


@api.route('/topics/<uuid:topic_id>/type/<type_id>/status',
           methods=['GET'])
@decorators.login_required
@decorators.check_roles
def get_jobs_status_from_components(user, topic_id, type_id):

    # List of job meaningfull job status for global overview
    #
    # ie. If current job status is running, we should retrieve status
    # from prior job.
    valid_status = ['failure', 'success']

    topic_id = v1_utils.verify_existence_and_get(topic_id, _TABLE, get_id=True)
    v1_utils.verify_team_in_topic(user, topic_id)

    # Get list of all remotecis that are attached to a topic this type belongs
    # to
    fields = [models.REMOTECIS.c.id.label('remoteci_id'),
              models.REMOTECIS.c.name.label('remoteci_name'),
              models.TEAMS.c.id.label('team_id'),
              models.TEAMS.c.name.label('team_name'),
              models.TOPICS.c.name.label('topic_name'),
              models.COMPONENTS.c.id.label('component_id'),
              models.COMPONENTS.c.name.label('component_name'),
              models.COMPONENTS.c.type.label('component_type'),
              models.JOBS.c.id.label('job_id'),
              models.JOBS.c.status.label('job_status'),
              models.JOBS.c.created_at.label('job_created_at')]
    query = (sql.select(fields)
             .select_from(
                 sql.join(
                     models.REMOTECIS,
                     models.JOBS,
                     models.REMOTECIS.c.id == models.JOBS.c.remoteci_id,
                     isouter=True)
             .join(
                 models.JOIN_JOBS_COMPONENTS,
                 models.JOIN_JOBS_COMPONENTS.c.job_id == models.JOBS.c.id)
             .join(
                 models.COMPONENTS,
                 models.COMPONENTS.c.id == models.JOIN_JOBS_COMPONENTS.c.component_id)  # noqa
             .join(
                 models.TOPICS,
                 models.TOPICS.c.id == models.COMPONENTS.c.topic_id)
             .join(
                 models.TEAMS,
                 models.TEAMS.c.id == models.JOBS.c.team_id))
             .where(
                 sql.and_(
                     models.REMOTECIS.c.state == 'active',
                     models.TEAMS.c.external == True,  # noqa
                     models.JOBS.c.status.in_(valid_status),
                     models.JOBS.c.state != 'archived',
                     models.COMPONENTS.c.type == type_id,
                     models.TOPICS.c.id == topic_id))
             .order_by(
                 models.REMOTECIS.c.id,
                 models.JOBS.c.created_at.desc())
             .distinct(models.REMOTECIS.c.id))

    if not user.is_super_admin():
        query.append_whereclause(models.TEAMS.c.id.in_(user.teams))
    rcs = flask.g.db_conn.execute(query).fetchall()
    nb_row = len(rcs)

    return flask.jsonify({'jobs': rcs,
                          '_meta': {'count': nb_row}})


@api.route('/topics/<uuid:topic_id>/tests', methods=['GET'])
@decorators.login_required
@decorators.check_roles
def get_all_tests(user, topic_id):
    args = schemas.args(flask.request.args.to_dict())
    if not user.is_read_only_user():
        v1_utils.verify_team_in_topic(user, topic_id)
    v1_utils.verify_existence_and_get(topic_id, _TABLE)

    query = sql.select([models.TESTS]).\
        select_from(models.JOIN_TOPICS_TESTS.join(models.TESTS)).\
        where(models.JOIN_TOPICS_TESTS.c.topic_id == topic_id)

    T_COLUMNS = v1_utils.get_columns_name_with_objects(models.TESTS)
    sort_list = v1_utils.sort_query(args['sort'], T_COLUMNS)
    where_list = v1_utils.where_query(args['where'], models.TESTS, T_COLUMNS)

    query = v1_utils.add_sort_to_query(query, sort_list)
    query = v1_utils.add_where_to_query(query, where_list)
    if args.get('limit', None):
        query = query.limit(args.get('limit'))
    if args.get('offset', None):
        query = query.offset(args.get('offset'))

    rows = flask.g.db_conn.execute(query).fetchall()

    query_nb_rows = sql.select([func.count(models.TESTS.c.id)]). \
        select_from(models.JOIN_TOPICS_TESTS.join(models.TESTS)). \
        where(models.JOIN_TOPICS_TESTS.c.topic_id == topic_id)
    nb_rows = flask.g.db_conn.execute(query_nb_rows).scalar()

    res = flask.jsonify({'tests': rows,
                         '_meta': {'count': nb_rows}})
    res.status_code = 200
    return res


@api.route('/topics/<uuid:topic_id>/tests', methods=['POST'])
@decorators.login_required
@decorators.check_roles
def add_test_to_topic(user, topic_id):
    if not auth.is_admin(user):
        raise auth.UNAUTHORIZED
    # todo(yassine): enforce test_id presence in the data
    data_json = flask.request.json
    values = {'topic_id': topic_id,
              'test_id': data_json.get('test_id', None)}

    v1_utils.verify_existence_and_get(topic_id, _TABLE)

    query = models.JOIN_TOPICS_TESTS.insert().values(**values)
    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(_TABLE.name,
                                          'topic_id, test_id')
    result = json.dumps(values)
    return flask.Response(result, 201, content_type='application/json')


@api.route('/topics/<uuid:t_id>/tests/<uuid:test_id>', methods=['DELETE'])
@decorators.login_required
@decorators.check_roles
def delete_test_from_topic(user, t_id, test_id):
    if not auth.is_admin(user):
        v1_utils.verify_team_in_topic(user, t_id)
    v1_utils.verify_existence_and_get(test_id, models.TESTS)

    JTT = models.JOIN_TOPICS_TESTS
    where_clause = sql.and_(JTT.c.topic_id == t_id,
                            JTT.c.test_id == test_id)
    query = JTT.delete().where(where_clause)
    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict('Test', test_id)

    return flask.Response(None, 204, content_type='application/json')


# teams set apis
@api.route('/topics/<uuid:topic_id>/teams', methods=['POST'])
@decorators.login_required
@decorators.check_roles
def add_team_to_topic(user, topic_id):
    # TODO(yassine): use voluptuous schema
    data_json = flask.request.json
    team_id = data_json.get('team_id')

    topic = v1_utils.verify_existence_and_get(topic_id, _TABLE)
    team_id = v1_utils.verify_existence_and_get(team_id, models.TEAMS,
                                                get_id=True)

    if not user.is_super_admin() and \
       not (user.is_team_product_owner(team_id) and
            user.product_id == topic['product_id']):
        raise auth.UNAUTHORIZED

    values = {'topic_id': topic['id'],
              'team_id': team_id}
    query = models.JOINS_TOPICS_TEAMS.insert().values(**values)
    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(models.JOINS_TOPICS_TEAMS.name,
                                          'team_id, topic_id')

    result = json.dumps(values)
    return flask.Response(result, 201, content_type='application/json')


@api.route('/topics/<uuid:topic_id>/teams/<uuid:team_id>', methods=['DELETE'])
@decorators.login_required
@decorators.check_roles
def delete_team_from_topic(user, topic_id, team_id):
    topic = v1_utils.verify_existence_and_get(topic_id, _TABLE)
    team_id = v1_utils.verify_existence_and_get(team_id, models.TEAMS,
                                                get_id=True)

    if not user.is_super_admin() and \
       not (user.is_team_product_owner(team_id) and
            user.product_id == topic['product_id']):
        raise auth.UNAUTHORIZED

    JTT = models.JOINS_TOPICS_TEAMS
    where_clause = sql.and_(JTT.c.topic_id == topic['id'],
                            JTT.c.team_id == team_id)
    query = JTT.delete().where(where_clause)
    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict('Topics_teams', team_id)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/topics/<uuid:topic_id>/teams', methods=['GET'])
@decorators.login_required
@decorators.check_roles
def get_all_teams_from_topic(user, topic_id):
    topic = v1_utils.verify_existence_and_get(topic_id, _TABLE)

    if not user.is_super_admin() and \
       not user.product_id == topic['product_id']:
        raise auth.UNAUTHORIZED

    # Get all teams which belongs to a given topic
    JTT = models.JOINS_TOPICS_TEAMS
    query = (sql.select([models.TEAMS])
             .select_from(JTT.join(models.TEAMS))
             .where(JTT.c.topic_id == topic['id']))
    rows = flask.g.db_conn.execute(query)

    res = flask.jsonify({'teams': rows,
                         '_meta': {'count': rows.rowcount}})
    return res


@api.route('/topics/purge', methods=['GET'])
@decorators.login_required
@decorators.check_roles
def get_to_purge_archived_topics(user):
    return base.get_to_purge_archived_resources(user, _TABLE)


@api.route('/topics/purge', methods=['POST'])
@decorators.login_required
@decorators.check_roles
def purge_archived_topics(user):
    return base.purge_archived_resources(user, _TABLE)
