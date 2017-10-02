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

from dci import auth
from sqlalchemy import sql
from dci.api.v1 import utils as v1_utils
from dci.common import exceptions as dci_exc
from dci.common import schemas


def get_resource_by_id(user, resource, table, embed_many, ignore_columns=None,
                       resource_name=None):
    args = schemas.args(flask.request.args.to_dict())
    resource_name = resource_name or table.name[0:-1]
    resource_id = resource['id']
    columns = v1_utils.get_columns_name_with_objects(table)

    query = v1_utils.QueryBuilder(table, args, columns, ignore_columns)

    if not user.is_super_admin() and 'team_id' in resource:
        query.add_extra_condition(table.c.team_id.in_(user.teams))

    if 'state' in resource:
        query.add_extra_condition(table.c.state != 'archived')

    query.add_extra_condition(table.c.id == resource_id)

    rows = query.execute(fetchall=True)
    rows = v1_utils.format_result(rows, table.name, args['embed'], embed_many)

    if len(rows) < 1:
        raise dci_exc.DCINotFound(resource_name, resource_id)
    resource = rows[0]

    res = flask.jsonify({resource_name: resource})

    if 'etag' in resource:
        res.headers.add_header('ETag', resource['etag'])

    return res


def get_to_purge_archived_resources(user, table):
    """List the entries to be purged from the database. """
    if not auth.is_admin(user):
        raise auth.UNAUTHORIZED

    where_clause = sql.and_(
        table.c.state == 'archived'
    )
    query = sql.select([table]).where(where_clause)
    result = flask.g.db_conn.execute(query).fetchall()

    return flask.jsonify({table.name: result,
                          '_meta': {'count': len(result)}})


def purge_archived_resources(user, table):
    """Remove the entries to be purged from the database. """

    if not auth.is_admin(user):
        raise auth.UNAUTHORIZED

    where_clause = sql.and_(
        table.c.state == 'archived'
    )
    query = table.delete().where(where_clause)
    flask.g.db_conn.execute(query)

    return flask.Response(None, 204, content_type='application/json')
