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
from dci.api.v1 import components
from dci.api.v1 import jobdefinitions
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import models

# associate column names with the corresponding SA Column object
_TABLE = models.TOPICS
_T_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)


@api.route('/topics', methods=['POST'])
@auth.requires_auth
def create_topics(user):
    values = schemas.topic.post(flask.request.json)

    if not(auth.is_admin(user)):
        raise auth.UNAUTHORIZED

    etag = utils.gen_etag()
    values.update({
        'id': utils.gen_uuid(),
        'created_at': datetime.datetime.utcnow().isoformat(),
        'updated_at': datetime.datetime.utcnow().isoformat(),
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

    topic_id = v1_utils.verify_existence_and_get(topic_id, _TABLE, get_id=True)
    v1_utils.verify_team_in_topic(user, topic_id)

    query = sql.select([_TABLE]).where(_TABLE.c.id == topic_id)
    topic = flask.g.db_conn.execute(query).fetchone()

    if topic is None:
        raise dci_exc.DCINotFound('Topic', topic_id)

    return flask.jsonify({'topic': topic})


@api.route('/topics', methods=['GET'])
@auth.requires_auth
def get_all_topics(user):
    args = schemas.args(flask.request.args.to_dict())
    # if the user is an admin then he can get all the topics
    if auth.is_admin(user):
        q_bd = v1_utils.QueryBuilder(_TABLE, args['offset'], args['limit'])

        q_bd.sort = v1_utils.sort_query(args['sort'], _T_COLUMNS)

        # get the number of rows for the '_meta' section
        nb_row = flask.g.db_conn.execute(q_bd.build_nb_row()).scalar()
        rows = flask.g.db_conn.execute(q_bd.build()).fetchall()

        return flask.jsonify({'topics': rows, '_meta': {'count': nb_row}})
    # otherwise the user will only get the topics on which his team
    # subscribed to
    else:
        team_id = user['team_id']
        JTT = models.JOINS_TOPICS_TEAMS
        # TODO(yassine): use QueryBuilder and sort
        query = (sql.select([models.TOPICS])
                 .select_from(JTT.join(models.TOPICS))
                 .where(JTT.c.team_id == team_id))
        query = query.limit(args['limit'])
        query = query.offset(args['offset'])

        rows = flask.g.db_conn.execute(query)

        res = flask.jsonify({'topics': rows,
                             '_meta': {'count': rows.rowcount}})
        res.status_code = 201
        return res


@api.route('/topics/<topic_id>', methods=['PUT'])
@auth.requires_auth
def put_topic(user, topic_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    values = schemas.topic.put(flask.request.json)

    if not(auth.is_admin(user)):
        raise auth.UNAUTHORIZED

    topic_id = v1_utils.verify_existence_and_get(topic_id, _TABLE, get_id=True)

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
    query = _TABLE.delete().where(_TABLE.c.id == topic_id)
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
    embed = schemas.args(flask.request.args.to_dict())['embed']
    topic_id = v1_utils.verify_existence_and_get(topic_id, _TABLE, get_id=True)
    v1_utils.verify_team_in_topic(user, topic_id)
    args = schemas.args(flask.request.args.to_dict())

    # if the user is not the admin then filter by team_id
    team_id = user['team_id'] if not auth.is_admin(user) else None

    EMBED = {
        'teams': v1_utils.embed(models.TEAMS),
        'teams_topics': v1_utils.embed(models.JOINS_TOPICS_TEAMS),
        'topics': v1_utils.embed(models.TOPICS),
    }

    # Get the last (by created_at field) component id of <type_id> type
    # within <topic_id> topic
    where_clause = sql.and_(models.COMPONENTS.c.type == type_id,
                            models.COMPONENTS.c.topic_id == topic_id,
                            models.COMPONENTS.c.active == True)
    q_bd = sql.select([models.COMPONENTS]).where(where_clause).order_by(
        sql.desc(models.COMPONENTS.c.created_at)).limit(1)
    cpt = flask.g.db_conn.execute(q_bd).fetchone()
    cpt_id = cpt['id']
    cpt_name = cpt['name']


    # Get list of all remotecis that are attached to a topic this type belongs
    # to
    q_bd = v1_utils.QueryBuilder(models.REMOTECIS, args['offset'], args['limit'],
                                 EMBED)
    q_bd.join(['teams', 'teams_topics', 'topics'])
    if team_id:
        q_bd.where.append(models.TEAMS.c.id == team_id)
    q_bd.where.append(models.TOPICS.c.id == topic_id)
    q_bd.where.append(models.REMOTECIS.c.active == True)
    rcs = flask.g.db_conn.execute(q_bd.build()).fetchall()
    rcs = [v1_utils.group_embedded_resources(embed, rc) for rc in rcs]

    to_return = []
    for rc in rcs:
        to_return.append(
            { 'team_id': rc['team_id'],
              'team_name': rc['teams_name'],
              'topic_id': topic_id,
              'topic_name': rc['topics_name'],
              'remoteci_id': rc['id'],
              'remoteci_name': rc['name'],
              'component_id': cpt_id,
              'component_name': cpt_name,
              'component_type': type_id,
              'job_status': None,
              'job_id': None,
              'job_created_at': None}
        )

    # Get status of last job with last component for all remotecis that
    # belongs to the topic
    jjc = (
        models.JOBS
        .join(
            models.JOIN_JOBS_COMPONENTS,
            models.JOBS.c.id == models.JOIN_JOBS_COMPONENTS.c.job_id
        )
        .join(
            models.REMOTECIS,
            models.JOBS.c.remoteci_id == models.REMOTECIS.c.id
        )
    )
    q_bd = (
        sql.select([models.JOBS])
        .select_from(jjc)
        .distinct(models.REMOTECIS.c.id)
        .where(models.JOIN_JOBS_COMPONENTS.c.component_id == cpt_id)
        .order_by(models.REMOTECIS.c.id, models.JOBS.c.created_at.desc())
    )
    rows = flask.g.db_conn.execute(q_bd).fetchall()
    results = [v1_utils.group_embedded_resources(embed, row) for row in rows]

    for rc in to_return:
        for result in results:
            if result['remoteci_id'] == rc['remoteci_id']:
                rc['job_status'] = result['status']
                rc['job_id'] = result['id']
                rc['job_created_at'] = result['created_at']
                break

    return flask.jsonify({'jobs': to_return, '_meta': {'count': len(to_return)}})


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
    if not(auth.is_admin(user)):
        v1_utils.verify_team_in_topic(user, topic_id)
    v1_utils.verify_existence_and_get(topic_id, _TABLE)

    TABLE = models.TESTS
    T_COLUMNS = v1_utils.get_columns_name_with_objects(TABLE)
    EMBED = {
        'topic_tests': v1_utils.embed(models.JOIN_TOPICS_TESTS)
    }

    q_bd = v1_utils.QueryBuilder(TABLE, args['offset'], args['limit'], EMBED)
    q_bd.join(['topic_tests'])
    q_bd.sort = v1_utils.sort_query(args['sort'], T_COLUMNS)
    q_bd.where = v1_utils.where_query(args['where'], TABLE, T_COLUMNS)

    # get the number of rows for the '_meta' section
    nb_row = flask.g.db_conn.execute(q_bd.build_nb_row()).scalar()
    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()

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
