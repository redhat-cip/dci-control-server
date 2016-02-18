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
import six
from sqlalchemy import sql, func

from dci.common import exceptions as dci_exc
from dci.common import utils
from dci.db import models


def verify_existence_and_get(id, table):
    """Verify the existence of a resource in the database and then
    return it if it exists, according to the condition, or raise an
    exception.
    """
    if 'name' in table.columns:
        where_clause = sql.or_(table.c.id == id, table.c.name == id)
    else:
        where_clause = table.c.id == id

    query = sql.select([table]).where(where_clause)
    result = flask.g.db_conn.execute(query).fetchone()

    if result is None:
        raise dci_exc.DCIException('Resource "%s" not found.' % id,
                                   status_code=404)
    return result


def verify_team_in_topic(user, topic_id):
    team_id = user['team_id']
    belongs_to_topic_q = (
        sql.select([models.JOINS_TOPICS_TEAMS.c.team_id]).where(
            sql.expression.and_(
                models.JOINS_TOPICS_TEAMS.c.team_id == team_id,  # noqa
                models.JOINS_TOPICS_TEAMS.c.topic_id == topic_id)  # noqa
        ))
    belongs_to_topic = flask.g.db_conn.execute(belongs_to_topic_q).fetchone()
    if not belongs_to_topic:
        raise dci_exc.DCIException('User team does not belongs to topic %s.'
                                   % topic_id, status_code=412)


def verify_embed_list(embed_list, valid_embedded_resources):
    """Verify the embed list according the supported valid list. If it's not
    valid then raise an exception.
    """
    for resource in embed_list:
        if resource not in valid_embedded_resources:
            raise dci_exc.DCIException(
                "Invalid embed list: '%s'" % embed_list,
                payload={'Valid elements': list(valid_embedded_resources)})


def get_query_with_join(embed_list, valid_embedded_resources):
    """Given a select query on one table columns and a list of tables to_join
    with, this unction construct the correct sqlalchemy query to make a join.
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
    select = []
    for prefix, table in six.iteritems(resources_to_embed):
        select.extend(_flatten_columns_with_prefix(prefix, table))

    # order is important for the SQL join
    join = [item[1] for item in sorted(resources_to_embed.items())]

    return select, join


def group_embedded_resources(items_to_embed, row):
    """Given the embed list and a row this function group the items by embedded
    element. Handle dot notation for nested fields.

    For instance:
        - embed_list = ['a', 'b', 'a.c']
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
    def nestify(item_to_embed, row):
        result_tmp = {}
        row_tmp = {}

        # build the two possible keys for nested values
        underscore_key = item_to_embed + '_'
        point_key = item_to_embed + '.'

        for key, value in row.items():
            if key.startswith(underscore_key) or key.startswith(point_key):
                # if the element is a nested one, add it to result_tmp with
                # the truncated key
                key = key[len(item_to_embed) + 1:]
                result_tmp[key] = value
            else:
                # if not, store the value to replace the row in order to
                # avoid processing duplicate values
                row_tmp[key] = value
        return result_tmp, row_tmp

    if row is None:
        return None
    if not items_to_embed:
        return dict(row)

    # output of the function
    res = {}
    items_to_embed.sort()
    for item_to_embed in items_to_embed:
        if '.' in item_to_embed:
            # if a nested element appears i.e: jobdefinition.test
            container, nested = item_to_embed.split('.')
            # run nestify on the container element with the nested key
            nested_values, container_values = nestify(nested, res[container])
            # rebuild res and put nested into its container
            # i.e: test into jobdefinition
            container_values[nested] = nested_values
            res[container] = container_values
        else:
            # if no nested actualize res, and replace row with
            # unprocessed values
            res[item_to_embed], row = nestify(item_to_embed, row)

    # merge top level values (not processed by nestify)
    return utils.dict_merge(res, row)


def get_columns_name_with_objects(table):
    result = {}
    for column in table.columns:
        result[column.name] = getattr(table.c, column.name)
    return result


def sort_query(sort, valid_columns):
    order_by = []
    for sort_elem in sort:
        sort_order = (sql.desc
                      if sort_elem.startswith('-') else sql.asc)
        sort_elem = sort_elem.strip(' -')
        if sort_elem not in valid_columns:
            raise dci_exc.DCIException(
                'Invalid sort key: "%s"' % sort_elem,
                payload={'Valid sort keys': list(valid_columns.keys())}
            )
        order_by.append(sort_order(valid_columns[sort_elem]))
    return order_by


def where_query(where, table, columns):
    where_conds = []
    err_msg = 'Invalid where key: "%s"'
    for where_elem in where:
        try:
            name, value = where_elem.split(':', 1)
        except ValueError:
            payload = {'error': 'where key must have the following form '
                                '"key:value"'}
            raise dci_exc.DCIException(err_msg % where_elem, payload=payload)

        if name not in columns:
            payload = {'valid_keys': list(columns.keys())}
            raise dci_exc.DCIException(err_msg % name, payload=payload)

        m_column = getattr(table.c, name)
        # TODO(yassine): do the same for columns type different from string
        # if it's an Integer column, then try to cast the value
        if m_column.type.python_type == int:
            try:
                value = int(value)
            except ValueError:
                payload = {name: 'not integer'}
                raise dci_exc.DCIException(err_msg % name, payload=payload)

        where_conds.append(m_column == value)
    return where_conds


class QueryBuilder(object):

    def __init__(self, table, offset=None, limit=None):
        self.table = table
        self.offset = offset
        self.limit = limit
        self.sort = []
        self.where = []
        self.select = [table]
        self.join = []

    def build(self):
        query = sql.select(self.select)

        for where in self.where:
            query = query.where(where)

        for sort in self.sort:
            query = query.order_by(sort)

        if self.limit:
            query = query.limit(self.limit)

        if self.offset:
            query = query.offset(self.offset)

        if self.join:
            query_from = self.table
            for join in self.join:
                query_from = query_from.join(join)
            query = query.select_from(query_from)

        return query

    def build_nb_row(self):
        query = sql.select([func.count(self.table.c.id)])
        for where in self.where:
            query = query.where(where)

        if self.join:
            query_join = self.table
            for join in self.join:
                query_join = query_join.join(join)

            query = query.select_from(query_join)

        return query
