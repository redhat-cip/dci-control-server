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

from sqlalchemy import sql
from dci.api.v1 import utils as v1_utils
from dci.common import exceptions as dci_exc
from dci.common import signature
from dci.common import utils
from dci.common.schemas import check_and_get_args


def get_resource_by_id(user, resource, table, embed_many=None,
                       ignore_columns=None, resource_name=None, embeds=None,
                       jsonify=True):
    args = check_and_get_args(flask.request.args.to_dict())
    if embeds is not None:
        # make a copy of the list to avoid side effect
        args['embed'] = args['embed'] + list(embeds)
    resource_name = resource_name or table.name[0:-1]
    resource_id = resource['id']
    columns = v1_utils.get_columns_name_with_objects(table)

    query = v1_utils.QueryBuilder(table, args, columns, ignore_columns)

    if 'state' in resource:
        query.add_extra_condition(table.c.state != 'archived')

    query.add_extra_condition(table.c.id == resource_id)

    rows = query.execute(fetchall=True)
    rows = v1_utils.format_result(rows, table.name, args['embed'], embed_many)

    if len(rows) < 1:
        raise dci_exc.DCINotFound(resource_name, resource_id)
    resource = rows[0]

    if jsonify is True:
        res = flask.jsonify({resource_name: resource})
        if 'etag' in resource:
            res.headers.add_header('ETag', resource['etag'])
        return res
    else:
        return resource


def get_archived_resources(table):
    q_archived_files = v1_utils.QueryBuilder(table)
    q_archived_files.add_extra_condition(table.c.state == 'archived')
    return q_archived_files.execute(fetchall=True, use_labels=False)


def get_to_purge_archived_resources(user, table):
    """List the entries to be purged from the database. """

    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    archived_resources = get_archived_resources(table)

    return flask.jsonify({table.name: archived_resources,
                          '_meta': {'count': len(archived_resources)}})


def purge_archived_resources(user, table):
    """Remove the entries to be purged from the database. """

    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    where_clause = sql.and_(
        table.c.state == 'archived'
    )
    query = table.delete().where(where_clause)
    flask.g.db_conn.execute(query)

    return flask.Response(None, 204, content_type='application/json')


def refresh_api_secret(user, resource, table):
    """Refresh the resource API Secret. """

    resource_name = table.name[0:-1]

    where_clause = sql.and_(
        table.c.etag == resource['etag'],
        table.c.id == resource['id'],
    )

    values = {
        'api_secret': signature.gen_secret(),
        'etag': utils.gen_etag()
    }

    query = table.update().where(where_clause).values(**values)
    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict(resource_name, resource['id'])

    res = flask.jsonify(({'id': resource['id'], 'etag': resource['etag'],
                          'api_secret': values['api_secret']}))
    res.headers.add_header('ETag', values['etag'])
    return res
