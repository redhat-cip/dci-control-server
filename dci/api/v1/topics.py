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
from sqlalchemy import exc as sa_exc
from sqlalchemy import sql

from dci.api.v1 import api
from dci.api.v1 import components
from dci.api.v1 import jobdefinitions
from dci.api.v1 import tests
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


@api.route('/topics/<t_id>', methods=['GET'])
@auth.requires_auth
def get_topic_by_id_or_name(user, t_id):
    where_clause = sql.or_(_TABLE.c.id == t_id, _TABLE.c.name == t_id)

    query = sql.select([_TABLE]).where(where_clause)
    topic = flask.g.db_conn.execute(query).fetchone()

    if topic is None:
        raise dci_exc.DCINotFound('Topic', t_id)

    res = flask.jsonify({'topic': topic})
    return res


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


@api.route('/topics/<t_id>', methods=['DELETE'])
@auth.requires_auth
def delete_topic_by_id_or_name(user, t_id):
    if not(auth.is_admin(user)):
        raise auth.UNAUTHORIZED

    v1_utils.verify_existence_and_get(t_id, _TABLE)
    where_clause = sql.or_(_TABLE.c.id == t_id, _TABLE.c.name == t_id)
    query = _TABLE.delete().where(where_clause)
    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIDeleteConflict('Topic', t_id)

    return flask.Response(None, 204, content_type='application/json')


# components, jobdefinitions, tests GET
@api.route('/topics/<topic_id>/components', methods=['GET'])
@auth.requires_auth
def get_all_components(user, topic_id):
    v1_utils.verify_existence_and_get(topic_id, _TABLE)
    v1_utils.verify_team_in_topic(user, topic_id)
    return components.get_all_components(user, topic_id=topic_id)


@api.route('/topics/<topic_id>/jobdefinitions', methods=['GET'])
@auth.requires_auth
def get_all_jobdefinitions(user, topic_id):
    v1_utils.verify_team_in_topic(user, topic_id)
    return jobdefinitions.get_all_jobdefinitions(user, topic_id=topic_id)


@api.route('/topics/<topic_id>/tests', methods=['GET'])
@auth.requires_auth
def get_all_tests(user, topic_id):
    v1_utils.verify_team_in_topic(user, topic_id)
    return tests.get_all_tests(user, topic_id=topic_id)


# teams set apis
@api.route('/topics/<t_id>/teams', methods=['POST'])
@auth.requires_auth
def add_team_to_topic(user, t_id):
    if not(auth.is_admin(user)):
        raise auth.UNAUTHORIZED

    # TODO(yassine): use voluptuous schema
    data_json = flask.request.json
    values = {'topic_id': t_id,
              'team_id': data_json.get('team_id')}

    v1_utils.verify_existence_and_get(t_id, _TABLE)

    query = models.JOINS_TOPICS_TEAMS.insert().values(**values)
    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(models.JOINS_TOPICS_TEAMS.name,
                                          'team_id, topic_id')

    result = json.dumps(values)
    return flask.Response(result, 201, content_type='application/json')


@api.route('/topics/<t_id>/teams/<team_id>', methods=['DELETE'])
@auth.requires_auth
def delete_team_from_topic(user, t_id, team_id):
    if not(auth.is_admin(user)):
        raise auth.UNAUTHORIZED

    v1_utils.verify_existence_and_get(t_id, _TABLE)
    JTT = models.JOINS_TOPICS_TEAMS
    where_clause = sql.and_(JTT.c.topic_id == t_id,
                            JTT.c.team_id == team_id)
    query = JTT.delete().where(where_clause)
    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict('Topics_teams', team_id)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/topics/<t_id>/teams', methods=['GET'])
@auth.requires_auth
def get_all_teams_from_topic(user, t_id):
    if not(auth.is_admin(user)):
        raise auth.UNAUTHORIZED

    v1_utils.verify_existence_and_get(t_id, _TABLE)

    # Get all teams which belongs to a given topic
    JTT = models.JOINS_TOPICS_TEAMS
    query = (sql.select([models.TEAMS])
             .select_from(JTT.join(models.TEAMS))
             .where(JTT.c.topic_id == t_id))
    rows = flask.g.db_conn.execute(query)

    res = flask.jsonify({'teams': rows,
                         '_meta': {'count': rows.rowcount}})
    res.status_code = 201
    return res
