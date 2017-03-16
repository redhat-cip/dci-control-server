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
import uuid
from flask import json
from sqlalchemy import exc as sa_exc
from sqlalchemy import sql

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import components
from dci.api.v1 import jobdefinitions
from dci.api.v1 import tests
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import embeds
from dci.db import models

# associate column names with the corresponding SA Column object
_TABLE = models.TOPICS
_VALID_EMBED = embeds.topics()
_T_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)


@api.route('/topics', methods=['POST'])
@auth.requires_auth
def create_topics(user):
    created_at, updated_at = utils.get_dates(user)
    values = schemas.topic.post(flask.request.json)

    if not(auth.is_admin(user)):
        raise auth.UNAUTHORIZED

    etag = utils.gen_etag()
    values.update({
        'id': utils.gen_uuid(),
        'created_at': created_at,
        'updated_at': updated_at,
        'etag': etag
    })

    query = _TABLE.insert().values(**values)

    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(_TABLE.name, 'name')

    result = json.dumps({'topic': values})
    return flask.Response(result, 201, headers={'ETag': etag},
                          content_type='application/json')


@api.route('/topics/<topic_id>', methods=['GET'])
@auth.requires_auth
def get_topic_by_id_or_name(user, topic_id):

    embed = schemas.args(flask.request.args.to_dict())['embed']

    q_bd = v1_utils.QueryBuilder(_TABLE, embed=_VALID_EMBED)
    q_bd.join(embed)

    try:
        uuid.UUID(topic_id)
        q_bd.where.append(
            sql.and_(
                _TABLE.c.state != 'archived',
                _TABLE.c.id == topic_id
            )
        )
    except ValueError:
        q_bd.where.append(
            sql.and_(
                _TABLE.c.state != 'archived',
                _TABLE.c.name == topic_id
            )
        )

    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()
    rows = q_bd.dedup_rows(rows)
    if len(rows) != 1:
        raise dci_exc.DCINotFound('Topic', topic_id)
    topic = rows[0]
    v1_utils.verify_team_in_topic(user, topic['id'])
    return flask.jsonify({'topic': topic})


@api.route('/topics', methods=['GET'])
@auth.requires_auth
def get_all_topics(user):
    args = schemas.args(flask.request.args.to_dict())
    embed = args['embed']
    # if the user is an admin then he can get all the topics
    q_bd = v1_utils.QueryBuilder(_TABLE, args['offset'], args['limit'],
                                 _VALID_EMBED)
    q_bd.join(embed)
    q_bd.sort = v1_utils.sort_query(args['sort'], _T_COLUMNS,
                                    default='name')
    q_bd.where = v1_utils.where_query(args['where'], _TABLE, _T_COLUMNS)

    if not auth.is_admin(user):
        q_bd.where.append(_TABLE.c.id.in_(v1_utils.user_topic_ids(user)))

    q_bd.where.append(_TABLE.c.state != 'archived')
    # get the number of rows for the '_meta' section
    nb_row = flask.g.db_conn.execute(q_bd.build_nb_row()).scalar()
    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()
    rows = q_bd.dedup_rows(rows)

    return flask.jsonify({'topics': rows, '_meta': {'count': nb_row}})


@api.route('/topics/<topic_id>', methods=['PUT'])
@auth.requires_auth
def put_topic(user, topic_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    values = schemas.topic.put(flask.request.json)

    if not(auth.is_admin(user)):
        raise auth.UNAUTHORIZED

    def _verify_team_in_topic(user, topic_id):
        topic_id = v1_utils.verify_existence_and_get(topic_id, _TABLE,
                                                     get_id=True)
        # verify user's team in the topic
        v1_utils.verify_team_in_topic(user, topic_id)
        return topic_id

    topic_id = _verify_team_in_topic(user, topic_id)

    next_topic = values['next_topic']
    if next_topic:
        _verify_team_in_topic(user, next_topic)

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


@api.route('/topics/<topic_id>', methods=['DELETE'])
@auth.requires_auth
def delete_topic_by_id_or_name(user, topic_id):
    if not(auth.is_admin(user)):
        raise auth.UNAUTHORIZED

    topic_id = v1_utils.verify_existence_and_get(topic_id, _TABLE, get_id=True)

    values = {'state': 'archived'}
    where_clause = sql.and_(_TABLE.c.id == topic_id)
    query = _TABLE.update().where(where_clause).values(**values)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIDeleteConflict('Topic', topic_id)

    return flask.Response(None, 204, content_type='application/json')


# components, jobdefinitions, tests GET
@api.route('/topics/<topic_id>/components', methods=['GET'])
@auth.requires_auth
def get_all_components(user, topic_id):
    topic_id = v1_utils.verify_existence_and_get(topic_id, _TABLE, get_id=True)
    v1_utils.verify_team_in_topic(user, topic_id)
    return components.get_all_components(user, topic_id=topic_id)


@api.route('/topics/<topic_id>/components/<component_id>/jobs',
           methods=['GET'])
@auth.requires_auth
def get_jobs_from_components(user, topic_id, component_id):
    topic_id = v1_utils.verify_existence_and_get(topic_id, _TABLE, get_id=True)
    v1_utils.verify_team_in_topic(user, topic_id)
    v1_utils.verify_existence_and_get(component_id, models.COMPONENTS)

    # if the user is not the admin then filter by team_id
    team_id = user['team_id'] if not auth.is_admin(user) else None

    return components.get_jobs(user, component_id, team_id=team_id)


@api.route('/topics/<topic_id>/type/<type_id>/status',
           methods=['GET'])
@auth.requires_auth
def get_jobs_status_from_components(user, topic_id, type_id):

    # List of job meaningfull job status for global overview
    #
    # ie. If current job status is running, we should retrieve status
    # from prior job.
    valid_status = ['failure', 'product-failure', 'deployment-failure',
                    'success']

    topic_id = v1_utils.verify_existence_and_get(topic_id, _TABLE, get_id=True)
    v1_utils.verify_team_in_topic(user, topic_id)
    args = schemas.args(flask.request.args.to_dict())

    # if the user is not the admin then filter by team_id
    team_id = user['team_id'] if not auth.is_admin(user) else None

    # Get the last (by created_at field) component id of <type_id> type
    # within <topic_id> topic
    where_clause = sql.and_(models.COMPONENTS.c.type == type_id,
                            models.COMPONENTS.c.topic_id == topic_id,
                            models.COMPONENTS.c.state == 'active')
    q_bd = sql.select([models.COMPONENTS]).where(where_clause).order_by(
        sql.desc(models.COMPONENTS.c.created_at)).limit(1)
    cpt_id = flask.g.db_conn.execute(q_bd).fetchone()['id']

    # Get list of all remotecis that are attached to a topic this type belongs
    # to
    q_bd = v1_utils.QueryBuilder(models.REMOTECIS, args['offset'],
                                 args['limit'])
    j_subquery = sql.select([models.JOBS.join(
        models.JOIN_JOBS_COMPONENTS,
        sql.and_(
            models.JOIN_JOBS_COMPONENTS.c.job_id == models.JOBS.c.id,
            models.JOIN_JOBS_COMPONENTS.c.component_id == cpt_id,
        ))]).where(
        sql.and_(
            models.JOBS.c.remoteci_id == models.REMOTECIS.c.id,
            models.JOBS.c.status.in_(valid_status),
            models.JOBS.c.state != 'archived',
        )).order_by(
            models.JOBS.c.created_at.desc()).alias('job')
    q_bd.select = [
        models.REMOTECIS.c.id.label('remoteci_id'),
        models.REMOTECIS.c.name.label('remoteci_name'),
        models.TEAMS.c.id.label('team_id'),
        models.TEAMS.c.name.label('team_name'),
        models.TOPICS.c.name.label('topic_name'),
        models.COMPONENTS.c.id.label('component_id'),
        models.COMPONENTS.c.name.label('component_name'),
        models.COMPONENTS.c.type.label('component_type'),
        j_subquery.c.id.label('job_id'),
        j_subquery.c.status.label('job_status'),
        j_subquery.c.created_at.label('job_created_at'),
    ]
    q_bd._join += [
        models.REMOTECIS.join(j_subquery, isouter=True)
    ]
    q_bd.extra_where = [
        models.REMOTECIS.c.team_id == models.TEAMS.c.id,
        models.TOPICS.c.id == topic_id,
        models.COMPONENTS.c.id == cpt_id,
        models.REMOTECIS.c.state == 'active']
    q_bd.sort = [models.REMOTECIS.c.name]
    if team_id:
        q_bd.extra_where.append(models.TEAMS.c.id == team_id)
    nb_row = flask.g.db_conn.execute(q_bd.build_nb_row()).scalar()
    rcs = flask.g.db_conn.execute(q_bd.build()).fetchall()

    # NOTE(Gonéri): job_id should be renamed id to be consistent with
    # the other list that we return.
    return flask.jsonify({'jobs': rcs,
                          '_meta': {'count': nb_row}})


@api.route('/topics/<topic_id>/jobdefinitions', methods=['GET'])
@auth.requires_auth
def get_all_jobdefinitions_by_topic(user, topic_id):
    topic_id = v1_utils.verify_existence_and_get(topic_id, _TABLE, get_id=True)
    v1_utils.verify_team_in_topic(user, topic_id)
    return jobdefinitions._get_all_jobdefinitions(user, topic_id=topic_id)


@api.route('/topics/<topic_id>/tests', methods=['GET'])
@auth.requires_auth
def get_all_tests(user, topic_id):
    args = schemas.args(flask.request.args.to_dict())
    embed = args['embed']
    if not(auth.is_admin(user)):
        v1_utils.verify_team_in_topic(user, topic_id)
    v1_utils.verify_existence_and_get(topic_id, _TABLE)

    TABLE = models.TESTS
    T_COLUMNS = v1_utils.get_columns_name_with_objects(TABLE)

    q_bd = v1_utils.QueryBuilder(TABLE, args['offset'], args['limit'],
                                 tests._VALID_EMBED)
    q_bd.join(embed)
    q_bd._join.append(models.TESTS.join(
        models.JOIN_TOPICS_TESTS,
        models.JOIN_TOPICS_TESTS.c.topic_id == topic_id
    ))
    q_bd.sort = v1_utils.sort_query(args['sort'], T_COLUMNS)
    q_bd.where = v1_utils.where_query(args['where'], TABLE, T_COLUMNS)

    # get the number of rows for the '_meta' section
    nb_row = flask.g.db_conn.execute(q_bd.build_nb_row()).scalar()
    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()
    rows = q_bd.dedup_rows(rows)

    res = flask.jsonify({'tests': rows,
                         '_meta': {'count': nb_row}})
    res.status_code = 200
    return res


@api.route('/topics/<topic_id>/tests', methods=['POST'])
@auth.requires_auth
def add_test_to_topic(user, topic_id):
    if not(auth.is_admin(user)):
        raise auth.UNAUTHORIZED
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


@api.route('/topics/<t_id>/tests/<test_id>', methods=['DELETE'])
@auth.requires_auth
def delete_test_from_topic(user, t_id, test_id):
    if not(auth.is_admin(user)):
        v1_utils.verify_team_in_topic(user, t_id)
    v1_utils.verify_existence_and_get(test_id, _TABLE)

    JDC = models.JOIN_REMOTECIS_TESTS
    where_clause = sql.and_(JDC.c.topic_id == t_id,
                            JDC.c.test_id == test_id)
    query = JDC.delete().where(where_clause)
    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict('Test', test_id)

    return flask.Response(None, 204, content_type='application/json')


# teams set apis
@api.route('/topics/<topic_id>/teams', methods=['POST'])
@auth.requires_auth
def add_team_to_topic(user, topic_id):
    if not(auth.is_admin(user)):
        raise auth.UNAUTHORIZED

    # TODO(yassine): use voluptuous schema
    data_json = flask.request.json
    team_id = data_json.get('team_id')

    topic_id = v1_utils.verify_existence_and_get(topic_id, _TABLE, get_id=True)
    team_id = v1_utils.verify_existence_and_get(team_id, models.TEAMS,
                                                get_id=True)

    values = {'topic_id': topic_id,
              'team_id': team_id}
    query = models.JOINS_TOPICS_TEAMS.insert().values(**values)
    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(models.JOINS_TOPICS_TEAMS.name,
                                          'team_id, topic_id')

    result = json.dumps(values)
    return flask.Response(result, 201, content_type='application/json')


@api.route('/topics/<topic_id>/teams/<team_id>', methods=['DELETE'])
@auth.requires_auth
def delete_team_from_topic(user, topic_id, team_id):
    if not(auth.is_admin(user)):
        raise auth.UNAUTHORIZED

    topic_id = v1_utils.verify_existence_and_get(topic_id, _TABLE, get_id=True)
    team_id = v1_utils.verify_existence_and_get(team_id, models.TEAMS,
                                                get_id=True)

    JTT = models.JOINS_TOPICS_TEAMS
    where_clause = sql.and_(JTT.c.topic_id == topic_id,
                            JTT.c.team_id == team_id)
    query = JTT.delete().where(where_clause)
    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict('Topics_teams', team_id)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/topics/<topic_id>/teams', methods=['GET'])
@auth.requires_auth
def get_all_teams_from_topic(user, topic_id):
    if not(auth.is_admin(user)):
        raise auth.UNAUTHORIZED

    topic_id = v1_utils.verify_existence_and_get(topic_id, _TABLE, get_id=True)

    # Get all teams which belongs to a given topic
    JTT = models.JOINS_TOPICS_TEAMS
    query = (sql.select([models.TEAMS])
             .select_from(JTT.join(models.TEAMS))
             .where(JTT.c.topic_id == topic_id))
    rows = flask.g.db_conn.execute(query)

    res = flask.jsonify({'teams': rows,
                         '_meta': {'count': rows.rowcount}})
    res.status_code = 201
    return res


@api.route('/topics/purge', methods=['GET'])
@auth.requires_auth
def get_to_purge_archived_topics(user):
    return base.get_to_purge_archived_resources(user, _TABLE)


@api.route('/topics/purge', methods=['POST'])
@auth.requires_auth
def purge_archived_topics(user):
    return base.purge_archived_resources(user, _TABLE)
