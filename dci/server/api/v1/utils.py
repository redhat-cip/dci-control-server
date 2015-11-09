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

import flask
import sqlalchemy.sql

from dci.server.common import exceptions as dci_exc


def verify_existence_and_get(table, resource_id, cond_exist):
    """Verify the existence of a resource in the database and then
    return it if it exists, according to the condition, or raise an
    exception.
    """

    # remove the the last 's' character of the table name
    resource_name = table.name[:-1]
    query = sqlalchemy.sql.select([table]).where(cond_exist)

    result = flask.g.db_conn.execute(query).fetchone()

    if result is None:
        raise dci_exc.DCIException("%s type '%s' not found." %
                                   (resource_name, resource_id),
                                   status_code=404)
    return result


def verify_embed_list(embed_list, valid_embedded_resources):
    """Verify the embed list according the supported valid list. If it's not
    valid then raise an exception.
    """

    if embed_list == ['']:
        return

    for resource in embed_list:
        if resource not in valid_embedded_resources:
            raise dci_exc.DCIException(
                "Invalid embed list: '%s'" % embed_list,
                payload={'Valid elements': list(valid_embedded_resources)})


def get_query_with_join(table_a, *tables_to_join):
    """Give a table table_a and a list of tables tables tables_to_join, this
    function construct the correct sqlalchemy query to make a join.
    """

    def _flatten_columns_with_prefix(table):
        result = []
        # remove the last 's' character from the table name
        prefix = table.name[:-1]
        for c_name in table.c.keys():
            # Condition to avoid conflict when fetching the data because by
            # default there is the key 'prefix_id' when prefix is the table
            # name to join.
            if c_name != 'id':
                column_name_with_prefix = '%s_%s' % (prefix, c_name)
                result.append(table.c[c_name].label(column_name_with_prefix))
        return result

    # TODO(yassine): this code will evolve in order to
    # support a list of tables to join as in the Jobs table. For now it joins
    # only two tables.
    table_b = tables_to_join[0]
    q_select = _flatten_columns_with_prefix(table_b)
    q_select.append(table_a)
    return sqlalchemy.sql.select(q_select).select_from(table_a.join(table_b))


def group_embedded_resources(embed_list, row):
    """Given the embed list and a row this function group the items by embedded
    element.

    For instance:
        - embed_list = ['a', 'b']
        - row = {'id': '12', 'name' : 'lol',
                 'a_id': '123', 'a_name': 'lol2',
                 'b_id': '1234', 'b_name': 'lol3'}
    Output:
        {'id': '12', 'name': 'lol',
         'a': {'id': '123', 'name': 'lol2'},
         'b': {'id': '1234', 'name': 'lol3'}}
    """
    if row is None:
        return None
    if not embed_list:
        return dict(row)
    result = {}
    embed_list = [embed + '_' for embed in embed_list]

    for key, value in row.items():
        if any((key.startswith(embed) for embed in embed_list)):
            embd_elt_name, embd_elt_column = key.split('_', 1)
            embd_elt = result.get(embd_elt_name, {})
            embd_elt[embd_elt_column] = value
            result[embd_elt_name] = embd_elt
        else:
            result[key] = value
    return result


def get_columns_name_with_objects(table):
    result = {}
    for column in table.columns:
        result[column.name] = getattr(table.c, column.name)
    return result


def sort_query(query, sort_args, valid_columns):
    sort_list = sort_args.split(',')
    for sort_elem in sort_list:
        sort_order = (sqlalchemy.sql.desc
                      if sort_elem.startswith('-') else sqlalchemy.sql.asc)
        sort_elem = sort_elem.strip(' -')
        if sort_elem not in valid_columns:
            raise dci_exc.DCIException("Invalid sort key: '%s'" % sort_elem,
                                       payload={'Valid sort keys':
                                                list(valid_columns.keys())})
        query = query.order_by(sort_order(valid_columns[sort_elem]))
    return query


def where_query(query, where_args, table, columns):
    where_list = where_args.split(',')
    for where_elem in where_list:
        name, value = where_elem.split(':', 1)
        if name not in columns:
            raise dci_exc.DCIException("Invalid where key: '%s'" % name,
                                       payload={'Valid where keys':
                                                list(columns.keys())})
        m_column = getattr(table.c, name)
        # TODO(yassine): do the same for columns type different from string
        # if it's an Integer column, then try to cast the value
        if m_column.type.python_type == int:
            try:
                value = int(value)
            except ValueError:
                raise dci_exc.DCIException("Invalid where key: '%s'" % name,
                                           payload={name: 'not integer'})
        query = query.where(m_column == value)
    return query
