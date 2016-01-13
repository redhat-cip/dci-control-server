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
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import models

# associate column names with the corresponding SA Column object
_TABLE = models.COMPONENTS
_C_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)


@api.route('/components', methods=['POST'])
@auth.requires_auth
def create_components(user):
    etag = utils.gen_etag()
    values = schemas.component.post(flask.request.json)
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

    result = json.dumps({'component': values})
    return flask.Response(result, 201, headers={'ETag': etag},
                          content_type='application/json')


@api.route('/components', methods=['GET'])
@auth.requires_auth
def get_all_components(user, ct_id=None):
    """Get all components.

    If ct_id is not None, then return all the components with a type
    pointed by ct_id.
    """
    # get the diverse parameters
    args = schemas.args(flask.request.args.to_dict())

    q_bd = v1_utils.QueryBuilder(_TABLE, args['offset'], args['limit'])

    q_bd.sort = v1_utils.sort_query(args['sort'], _C_COLUMNS)
    q_bd.where = v1_utils.where_query(args['where'], _TABLE, _C_COLUMNS)

    # used for counting the number of rows when ct_id is not None
    if ct_id is not None:
        q_bd.where.append(_TABLE.c.componenttype_id == ct_id)

    nb_row = flask.g.db_conn.execute(q_bd.build_nb_row()).scalar()
    rows = flask.g.db_conn.execute(q_bd.build()).fetchall()

    return flask.jsonify({'components': rows, '_meta': {'count': nb_row}})


@api.route('/components/<c_id>', methods=['GET'])
@auth.requires_auth
def get_component_by_id_or_name(user, c_id):
    where_clause = sql.or_(_TABLE.c.id == c_id,
                           _TABLE.c.name == c_id)

    query = sql.select([_TABLE]).where(where_clause)

    component = flask.g.db_conn.execute(query).fetchone()
    if component is None:
        raise dci_exc.DCINotFound('Component', c_id)

    res = flask.jsonify({'component': component})
    res.headers.add_header('ETag', component['etag'])
    return res


@api.route('/components/<c_id>', methods=['DELETE'])
@auth.requires_auth
def delete_component_by_id_or_name(user, c_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    v1_utils.verify_existence_and_get(c_id, _TABLE)

    where_clause = sql.and_(
        _TABLE.c.etag == if_match_etag,
        sql.or_(_TABLE.c.id == c_id, _TABLE.c.name == c_id)
    )

    query = _TABLE.delete().where(where_clause)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIDeleteConflict('Component', c_id)

    return flask.Response(None, 204, content_type='application/json')
