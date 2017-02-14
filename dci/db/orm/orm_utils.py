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

from sqlalchemy.orm import *
from sqlalchemy import inspect
from sqlalchemy import desc
from dci.common import exceptions as dci_exc

def std_query(table, query, args):
    if table.state:
        query = query.filter(table.state != 'archived')
    if args['embed']:
        for join in args['embed']:
            query = query.options(joinedload(join))
    if args['where']:
        query = where_query(table, args['where'], query)
    if args['sort']:
        for sort in args['sort']:
            if sort[:1] == "-":
                query = query.order_by(desc(sort[1:]))
            else:
                query = query.order_by(sort)
    else:
        query = query.order_by('created_at')
    if args['offset']:
        query = query.offset(args['offset'])
    if args['limit']:
        query = query.limit(args['limit'])
    return query

def where_query(table, where, query):
    where_conds = []
    err_msg = 'Invalid where key: "%s"'
    for where_elem in where:
        try:
            name, value = where_elem.split(':', 1)
        except ValueError:
            payload = {'error': 'where key must have the following form '
                                '"key:value"'}
            raise dci_exc.DCIException(err_msg % where_elem, payload=payload)

        # we grab all interesting thing about the table (columns names, etc...)
        insp = inspect(table)
        # columns are grabbed with the table name before "users.id"
        # so we calculate the length to be able to compare the right thing
        tablename_len = len(str(insp.local_table.name))+1

        # We check if the where clause is set on a valid column
        for column in list(insp.columns):
            if column.name[:tablename_len] == name:
                m_column = column
                break

        # TODO(cedric) Cleanup the block
        # if m_column:
        #     payload = {'valid_keys': [column for column in list(insp.columns)]}
        #     raise dci_exc.DCIException(err_msg % name, payload=payload)

        query = query.filter(m_column == value)
    return query
