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
import sqlalchemy
from sqlalchemy import exc as sa_exc
from sqlalchemy import sql

from dci.api.v1 import api
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import models

_TABLE = models.JOBDEFINITIONS
# associate column names with the corresponding SA Column object
_JD_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)
_VALID_EMBED = {
}


@api.route('/jobdefinitions', methods=['POST'])
@auth.requires_auth
def create_jobdefinitions(user):
    etag = utils.gen_etag()
    data_json = schemas.jobdefinition.post(flask.request.json)
    data_json.update({
        'id': utils.gen_uuid(),
        'created_at': datetime.datetime.utcnow().isoformat(),
        'updated_at': datetime.datetime.utcnow().isoformat(),
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


def get_all_jobdefinitions(user, topic_id):
    """Get all jobdefinitions.

    If t_id is not None, then return all the jobdefinitions with a test
    pointed by t_id.
    """
    # get the diverse parameters
    args = schemas.args(flask.request.args.to_dict())
    embed = args['embed']

    v1_utils.verify_embed_list(embed, _VALID_EMBED.keys())

    q_bd = v1_utils.QueryBuilder(_TABLE, args['offset'], args['limit'])

    select, join = v1_utils.get_query_with_join(embed, _VALID_EMBED)
    q_bd.select.extend(select)
    q_bd.join.extend(join)

    q_bd.sort = v1_utils.sort_query(args['sort'], _JD_COLUMNS)
    q_bd.where = v1_utils.where_query(args['where'], _TABLE, _JD_COLUMNS)
    q_bd.where.append(_TABLE.c.topic_id == topic_id)

    # get the number of rows for the '_meta' section
    nb_row = flask.g.db_conn.execute(q_bd.build_nb_row()).scalar()
    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()

    rows = [v1_utils.group_embedded_resources(embed, row) for row in rows]

    return flask.jsonify({'jobdefinitions': rows, '_meta': {'count': nb_row}})


@api.route('/jobdefinitions/<jd_id>', methods=['GET'])
@auth.requires_auth
def get_jobdefinition_by_id_or_name(user, jd_id):
    # get the diverse parameters
    embed = schemas.args(flask.request.args.to_dict())['embed']
    v1_utils.verify_embed_list(embed, _VALID_EMBED.keys())

    q_bd = v1_utils.QueryBuilder(_TABLE)

    select, join = v1_utils.get_query_with_join(embed, _VALID_EMBED)
    q_bd.select.extend(select)
    q_bd.join.extend(join)

    where_clause = sql.or_(_TABLE.c.id == jd_id, _TABLE.c.name == jd_id)
    q_bd.where.append(where_clause)

    row = flask.g.db_conn.execute(q_bd.build()).fetchone()
    jobdefinition = v1_utils.group_embedded_resources(embed, row)

    if row is None:
        raise dci_exc.DCINotFound('Jobdefinition', jd_id)

    res = flask.jsonify({'jobdefinition': jobdefinition})
    res.headers.add_header('ETag', jobdefinition['etag'])
    return res


@api.route('/jobdefinitions/<jd_id>', methods=['PUT'])
@auth.requires_auth
def put_jobdefinition(user, jd_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    values = schemas.jobdefinition.put(flask.request.json)

    if not(auth.is_admin(user) or auth.is_admin_user(user, jd_id)):
        raise auth.UNAUTHORIZED

    v1_utils.verify_existence_and_get(jd_id, _TABLE)

    values['etag'] = utils.gen_etag()
    where_clause = sql.and_(
        _TABLE.c.etag == if_match_etag,
        sql.or_(_TABLE.c.id == jd_id, _TABLE.c.name == jd_id)
    )
    query = _TABLE.update().where(where_clause).values(**values)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict('Jobdefinition', jd_id)

    return flask.Response(None, 204, headers={'ETag': values['etag']},
                          content_type='application/json')


@api.route('/jobdefinitions/<jd_id>', methods=['DELETE'])
@auth.requires_auth
def delete_jobdefinition_by_id_or_name(user, jd_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    v1_utils.verify_existence_and_get(jd_id, _TABLE)

    where_clause = sql.and_(
        _TABLE.c.etag == if_match_etag,
        sql.or_(_TABLE.c.id == jd_id, _TABLE.c.name == jd_id)
    )
    query = _TABLE.delete().where(where_clause)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIDeleteConflict('Jobdefinition', jd_id)

    return flask.Response(None, 204, content_type='application/json')


def get_jobdefinition_types(user, topic_id):
    """Get all jobdefinitions types.
    """

    # get the diverse parameters
    args = schemas.args(flask.request.args.to_dict())

    q_bd = v1_utils.QueryBuilder(_TABLE, args['offset'], args['limit'])
    q_bd.select = [sqlalchemy.distinct(_TABLE.c.type)]
    q_bd.where.append(_TABLE.c.topic_id == topic_id)

    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()
    rows = [r[0] for r in rows]

    return flask.jsonify({'types': rows, '_meta': {'count': len(rows)}})


# Controllers for jobdefinition and components management


@api.route('/jobdefinitions/<jd_id>/components', methods=['POST'])
@auth.requires_auth
def add_component_to_jobdefinitions(user, jd_id):
    data_json = flask.request.json
    values = {'jobdefinition_id': jd_id,
              'component_id': data_json.get('component_id', None)}

    v1_utils.verify_existence_and_get(jd_id, _TABLE)

    query = models.JOIN_JOBDEFINITIONS_COMPONENTS.insert().values(**values)
    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(_TABLE.name,
                                          'jobdefinition_id, component_id')
    result = json.dumps(values)
    return flask.Response(result, 201, content_type='application/json')


@api.route('/jobdefinitions/<jd_id>/components', methods=['GET'])
@auth.requires_auth
def get_all_components_from_jobdefinitions(user, jd_id):
    v1_utils.verify_existence_and_get(jd_id, _TABLE)

    # Get all components which belongs to a given jobdefinition
    JDC = models.JOIN_JOBDEFINITIONS_COMPONENTS
    query = (sql.select([models.COMPONENTS])
             .select_from(JDC.join(models.COMPONENTS))
             .where(JDC.c.jobdefinition_id == jd_id))
    rows = flask.g.db_conn.execute(query)

    res = flask.jsonify({'components': rows,
                         '_meta': {'count': rows.rowcount}})
    res.status_code = 201
    return res


@api.route('/jobdefinitions/<jd_id>/components/<c_id>', methods=['DELETE'])
@auth.requires_auth
def delete_component_from_jobdefinition(user, jd_id, c_id):
    v1_utils.verify_existence_and_get(jd_id, _TABLE)

    JDC = models.JOIN_JOBDEFINITIONS_COMPONENTS
    where_clause = sql.and_(JDC.c.jobdefinition_id == jd_id,
                            JDC.c.component_id == c_id)
    query = JDC.delete().where(where_clause)
    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict('Component', c_id)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/jobdefinitions/<jd_id>/tests', methods=['POST'])
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


@api.route('/jobdefinitions/<jd_id>/tests', methods=['GET'])
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


@api.route('/jobdefinitions/<jd_id>/tests/<t_id>', methods=['DELETE'])
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
