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
from flask import json
from sqlalchemy import exc as sa_exc
from sqlalchemy import sql

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import embeds
from dci.db import models

_TABLE = models.JOBDEFINITIONS
# associate column names with the corresponding SA Column object
_VALID_EMBED = embeds.jobdefinitions()
_JD_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)


@api.route('/jobdefinitions', methods=['POST'])
@auth.requires_auth
def create_jobdefinitions(user):
    created_at, updated_at = utils.get_dates(user)
    etag = utils.gen_etag()
    data_json = schemas.jobdefinition.post(flask.request.json)
    data_json.update({
        'id': utils.gen_uuid(),
        'created_at': created_at,
        'updated_at': updated_at,
        'etag': etag
    })

    query = _TABLE.insert().values(**data_json)
    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError as e:
        raise dci_exc.DCIException("Integrity error on 'test_id' field.",
                                   payload=str(e))

    result = json.dumps({'jobdefinition': data_json})
    return flask.Response(result, 201, headers={'ETag': etag},
                          content_type='application/json')


def _get_all_jobdefinitions(user, topic_id=None):
    """Get all jobdefinitions.

    If t_id is not None, then return all the jobdefinitions with a test
    pointed by t_id.
    """
    # get the diverse parameters
    args = schemas.args(flask.request.args.to_dict())
    embed = args['embed']

    q_bd = v1_utils.QueryBuilder(_TABLE, args['offset'], args['limit'],
                                 embed=_VALID_EMBED)
    q_bd.join(embed)
    q_bd.sort = v1_utils.sort_query(args['sort'], _JD_COLUMNS)
    q_bd.where = v1_utils.where_query(args['where'], _TABLE, _JD_COLUMNS)

    if topic_id is None and not auth.is_admin(user):
        q_bd._join.extend([models.TOPICS, models.JOINS_TOPICS_TEAMS])
        q_bd.where += [
            models.JOINS_TOPICS_TEAMS.c.team_id == user['team_id'],
            models.JOINS_TOPICS_TEAMS.c.topic_id == models.TOPICS.c.id,
            _TABLE.c.topic_id == models.TOPICS.c.id]
    elif topic_id is not None:
        q_bd.where.append(_TABLE.c.topic_id == topic_id)

    q_bd.where.append(_TABLE.c.state != 'archived')

    # get the number of rows for the '_meta' section
    nb_row = flask.g.db_conn.execute(q_bd.build_nb_row()).scalar()
    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()
    rows = q_bd.dedup_rows(rows)

    return flask.jsonify({'jobdefinitions': rows, '_meta': {'count': nb_row}})


@api.route('/jobdefinitions')
@auth.requires_auth
def get_all_jobdefinitions(user):
    return _get_all_jobdefinitions(user)


@api.route('/jobdefinitions/<uuid:jd_id>', methods=['GET'])
@auth.requires_auth
def get_jobdefinition_by_id_or_name(user, jd_id):
    # get the diverse parameters
    embed = schemas.args(flask.request.args.to_dict())['embed']

    q_bd = v1_utils.QueryBuilder(_TABLE, embed=_VALID_EMBED)
    q_bd.join(embed)

    q_bd.where.append(
        sql.and_(
            _TABLE.c.state != 'archived',
            _TABLE.c.id == jd_id
        )
    )

    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()
    rows = q_bd.dedup_rows(rows)
    if len(rows) != 1:
        raise dci_exc.DCINotFound('Jobdefinition', jd_id)
    jobdefinition = rows[0]

    res = flask.jsonify({'jobdefinition': jobdefinition})
    res.headers.add_header('ETag', jobdefinition['etag'])
    return res


@api.route('/jobdefinitions/<uuid:jd_id>', methods=['PUT'])
@auth.requires_auth
@auth.requires_team_admin
def put_jobdefinition(user, jd_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    values = schemas.jobdefinition.put(flask.request.json)

    v1_utils.verify_existence_and_get(jd_id, _TABLE)

    values['etag'] = utils.gen_etag()
    where_clause = sql.and_(
        _TABLE.c.etag == if_match_etag,
        _TABLE.c.id == jd_id
    )
    query = _TABLE.update().where(where_clause).values(**values)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict('Jobdefinition', jd_id)

    return flask.Response(None, 204, headers={'ETag': values['etag']},
                          content_type='application/json')


@api.route('/jobdefinitions/<uuid:jd_id>', methods=['DELETE'])
@auth.requires_auth
def delete_jobdefinition_by_id_or_name(user, jd_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    v1_utils.verify_existence_and_get(jd_id, _TABLE)

    values = {'state': 'archived'}
    where_clause = sql.and_(
        _TABLE.c.etag == if_match_etag,
        _TABLE.c.id == jd_id
    )
    query = _TABLE.update().where(where_clause).values(**values)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIDeleteConflict('Jobdefinition', jd_id)

    return flask.Response(None, 204, content_type='application/json')


# Controllers for jobdefinition and components management


@api.route('/jobdefinitions/<uuid:jd_id>/tests', methods=['POST'])
@auth.requires_auth
def add_test_to_jobdefinitions(user, jd_id):
    data_json = flask.request.json
    values = {'jobdefinition_id': jd_id,
              'test_id': data_json.get('test_id', None)}

    v1_utils.verify_existence_and_get(jd_id, _TABLE)

    query = models.JOIN_JOBDEFINITIONS_TESTS.insert().values(**values)
    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(_TABLE.name,
                                          'jobdefinition_id, test_id')
    result = json.dumps(values)
    return flask.Response(result, 201, content_type='application/json')


@api.route('/jobdefinitions/<uuid:jd_id>/tests', methods=['GET'])
@auth.requires_auth
def get_all_tests_from_jobdefinitions(user, jd_id):
    v1_utils.verify_existence_and_get(jd_id, _TABLE)

    # Get all components which belongs to a given jobdefinition
    JDC = models.JOIN_JOBDEFINITIONS_TESTS
    query = (sql.select([models.TESTS])
             .select_from(JDC.join(models.TESTS))
             .where(JDC.c.jobdefinition_id == jd_id))
    rows = flask.g.db_conn.execute(query)

    res = flask.jsonify({'tests': rows,
                         '_meta': {'count': rows.rowcount}})
    res.status_code = 201
    return res


@api.route('/jobdefinitions/<uuid:jd_id>/tests/<uuid:t_id>',
           methods=['DELETE'])
@auth.requires_auth
def delete_test_from_jobdefinition(user, jd_id, t_id):
    v1_utils.verify_existence_and_get(jd_id, _TABLE)

    JDC = models.JOIN_JOBDEFINITIONS_TESTS
    where_clause = sql.and_(JDC.c.jobdefinition_id == jd_id,
                            JDC.c.test_id == t_id)
    query = JDC.delete().where(where_clause)
    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict('Test', t_id)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/jobdefinitions/purge', methods=['GET'])
@auth.requires_auth
def get_purge_archived_jobdefinitions(user):
    return base.get_to_purge_archived_resources(user, _TABLE)


@api.route('/jobdefinitions/purge', methods=['POST'])
@auth.requires_auth
def purge_archived_jobdefinitions(user):
    return base.purge_archived_resources(user, _TABLE)
