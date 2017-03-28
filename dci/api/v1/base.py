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


def get_to_purge_archived_resources(user, table):
    """List the entries to be purged from the database. """

    where_clause = sql.and_(
        table.c.state == 'archived'
    )
    query = sql.select([table]).where(where_clause)
    result = flask.g.db_conn.execute(query).fetchall()

    return flask.jsonify({table.name: result,
                          '_meta': {'count': len(result)}})


def purge_archived_resources(user, table):
    """Remove the entries to be purged from the database. """

    where_clause = sql.and_(
        table.c.state == 'archived'
    )
    query = table.delete().where(where_clause)
    flask.g.db_conn.execute(query)

    return flask.Response(None, 204, content_type='application/json')
