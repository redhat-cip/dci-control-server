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

import collections

import flask
import six
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
        raise dci_exc.DCIException("%s '%s' not found." %
                                   (resource_name, resource_id),
                                   status_code=404)
    return result


def verify_embed_list(embed_list, valid_embedded_resources):
    """Verify the embed list according the supported valid list. If it's not
    valid then raise an exception.
    """
    for resource in embed_list:
        if resource not in valid_embedded_resources:
            raise dci_exc.DCIException(
                "Invalid embed list: '%s'" % embed_list,
                payload={'Valid elements': list(valid_embedded_resources)})


def get_query_with_join(table_a, embed_list, valid_embedded_resources):
    """Give a table table_a and a list of tables tables tables_to_join, this
    function construct the correct sqlalchemy query to make a join.
    """

    def _flatten_columns_with_prefix(prefix, table):
        result = []
        # remove the last 's' character from the table name
        for c_name in table.c.keys():
            # Condition to avoid conflict when fetching the data because by
            # default there is the key 'prefix_id' when prefix is the table
            # name to join.
            if c_name != 'id':
                column_name_with_prefix = '%s_%s' % (prefix, c_name)
                result.append(table.c[c_name].label(column_name_with_prefix))
        return result

    verify_embed_list(embed_list, valid_embedded_resources.keys())

    resources_to_embed = {elem: valid_embedded_resources[elem]
                          for elem in embed_list}

    # flatten all tables for the SQL select
    query_select = [table_a]
    for prefix, table in six.iteritems(resources_to_embed):
        query_select.extend(_flatten_columns_with_prefix(prefix, table))

    # chain SQL join on all tables
    query_join = table_a
    # order is important for the SQL join
    resources_to_embed_ordered = \
        collections.OrderedDict(sorted(resources_to_embed.items()))
    for table_to_join in six.itervalues(resources_to_embed_ordered):
        query_join = query_join.join(table_to_join)

    return sqlalchemy.sql.select(query_select).select_from(query_join)


def group_embedded_resources(items_to_embed, row):
    """Given the embed list and a row this function group the items by embedded
    element. Handle dot notation for nested fields.

    For instance:
        - embed_list = ['a', 'b']
        - row = {'id': '12', 'name' : 'lol',
                 'a_id': '123', 'a_name': 'lol2', 'a_c_id': '12345',
                 'b_id': '1234', 'b_name': 'lol3',
                 'a.c_name': 'mdr1'}
    Output:
        {'id': '12', 'name': 'lol',
         'a': {'id': '123', 'name': 'lol2',
               'c': {'name': 'mdr1', 'id': '12345'}},
         'b': {'id': '1234', 'name': 'lol3'}}
    """
    if row is None:
        return None
    if not items_to_embed:
        return dict(row)
    result = {}
    items_to_embed_with_suffix = [item + '_' for item in items_to_embed]

    for key, value in row.items():
        if any((key.startswith(item) for item in items_to_embed_with_suffix)):
            embd_elt_name, embd_elt_column = key.split('_', 1)
            embd_elt = result.get(embd_elt_name, {})
            embd_elt[embd_elt_column] = value
            result[embd_elt_name] = embd_elt
        else:
            result[key] = value

    for embed_item in items_to_embed:
        if '.' in embed_item:
            # split the embed element from its nested element
            # ie. jobdefinition.test -> jobdefinition, test
            elem, nested_elem = embed_item.split('.', 1)

            # copy the the nested element into its right place
            # ie jobdefinition['test'] = ...
            result[elem][nested_elem] = result[embed_item]
            # add the id of the nested elem
            nested_elem_id = nested_elem + '_id'
            result[elem][nested_elem]['id'] = result[elem][nested_elem_id]
            # remove the nested elem id
            del result[elem][nested_elem_id]
            # remove the nested elem from the global result
            del result[embed_item]

    return result


def get_columns_name_with_objects(table):
    result = {}
    for column in table.columns:
        result[column.name] = getattr(table.c, column.name)
    return result


def sort_query(query, sort, valid_columns):
    for sort_elem in sort:
        sort_order = (sqlalchemy.sql.desc
                      if sort_elem.startswith('-') else sqlalchemy.sql.asc)
        sort_elem = sort_elem.strip(' -')
        if sort_elem not in valid_columns:
            raise dci_exc.DCIException("Invalid sort key: '%s'" % sort_elem,
                                       payload={'Valid sort keys':
                                                list(valid_columns.keys())})
        query = query.order_by(sort_order(valid_columns[sort_elem]))
    return query


def where_query(query, where, table, columns):
    for where_elem in where:
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
