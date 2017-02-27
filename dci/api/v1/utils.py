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
import six
from sqlalchemy import sql, func
from sqlalchemy import Table as sa_Table
from sqlalchemy.sql import text
from sqlalchemy.sql import and_

from dci.api.v1 import embeds
from dci import auth
from dci.common import exceptions as dci_exc
from dci.common import utils
from dci.db import models

import collections
import os


Embed = collections.namedtuple('Embed', [
    'many', 'select', 'where', 'sort', 'join'])


def embed(many=False, select=None, where=None,
          sort=None, join=None):
    """Prepare a Embed named tuple

    :param many: True if it's a one-to-many join
    :param select: an optional list of field to embed
    :param where: an extra WHERE clause
    :param sort: an extra ORDER BY clause
    :param join: an SQLAlchemy-core Join instance
    """
    return Embed(many, select, where, sort, join)


def verify_existence_and_get(id, table, get_id=False):
    """Verify the existence of a resource in the database and then
    return it if it exists, according to the condition, or raise an
    exception.
    """
    if 'name' in table.columns:
        where_clause = sql.or_(table.c.id == id, table.c.name == id)
    else:
        where_clause = table.c.id == id

    if 'state' in table.columns:
        where_clause = sql.and_(table.c.state != 'archived', where_clause)

    query = sql.select([table]).where(where_clause)
    result = flask.g.db_conn.execute(query).fetchone()

    if result is None:
        raise dci_exc.DCIException('Resource "%s" not found.' % id,
                                   status_code=404)
    if get_id:
        return result.id
    return result


def user_topic_ids(user):
    query = (
        sql.select([
            models.JOINS_TOPICS_TEAMS.c.topic_id,
        ]).select_from(models.JOINS_TOPICS_TEAMS)
        .where(models.JOINS_TOPICS_TEAMS.c.team_id == user['team_id']))

    rows = flask.g.db_conn.execute(query).fetchall()
    return [row[0] for row in rows]


def verify_team_in_topic(user, topic_id):
    """Verify that the user's team does belongs to the given topic. If
    the user is an admin then it belongs to all topics.
    """
    if auth.is_admin(user):
        return
    if topic_id not in user_topic_ids(user):
        raise dci_exc.DCIException('User team does not belongs to topic %s.'
                                   % topic_id, status_code=412)


def verify_user_in_team(user, team_id):
    """Verify that the user belongs to a given team. If the user is an
    admin then it belongs to all teams."""

    if auth.is_admin(user):
        return
    if not auth.is_in_team(user, team_id):
        raise dci_exc.DCIException('User\'s team does not belongs to '
                                   'team %s.' % team_id, status_code=412)


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
                key = key[len(item_to_embed) + 1:]
                result_tmp[key] = value
            else:
                # if not, store the value to replace the row in order to
                # avoid processing duplicate values
                row_tmp[key] = value
        if not result_tmp.get('id'):
            result_tmp = {}
        return result_tmp, row_tmp

    if row is None:
        return None
    if not items_to_embed:
        return dict(row)

    # output of the function
    res = {}
    # items_to_embed = list(set(items_to_embed))
    # items_to_embed.sort(key=lambda x: len(x.split('.')))
    # for item_to_embed in items_to_embed:
    for item_to_embed in sorted(set(items_to_embed)):
        if '.' in item_to_embed:
            # if a nested element appears i.e: jobdefinition.tests
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


def get_columns_name_with_objects(table, embed={}):
    columns = {
        column.name: getattr(table.c, column.name)
        for column in table.columns
    }
    for v in embed.values():
        for t in v.select:
            if hasattr(t, 'c'):
                for i in t.c:
                    columns[str(i)] = i
            else:
                columns[str(t)] = t
    return columns


def sort_query(sort, valid_columns, default='-created_at'):
    order_by = []
    if not sort:
        sort = [default]
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


def request_wants_html():
    best = (flask.request.accept_mimetypes
            .best_match(['text/html', 'application/json']))

    return (best == 'text/html' and
            flask.request.accept_mimetypes[best] >
            flask.request.accept_mimetypes['application/json'])


class QueryBuilder(object):

    def __init__(self, root_table, args, strings_to_columns, ignore_columns):
        self._root_table = root_table
        self._embeds = args.get('embed', None)
        self._limit = args.get('limit', None)
        self._offset = args.get('offset', None)
        self._sort = sort_query(args.get('sort', None), strings_to_columns)
        self._where = where_query(args.get('where', None), self._root_table,
                                  strings_to_columns)
        self._strings_to_columns = strings_to_columns
        self._extras_conditions = []
        self._ignored_columns = ignore_columns

    def add_extra_condition(self, condition):
        self._extras_conditions.append(condition)

    def _get_root_columns(self):
        # remove ignored columns
        columns_from_root_table = dict(self._strings_to_columns)
        for column_to_ignore in self._ignored_columns:
            columns_from_root_table.pop(column_to_ignore, None)
        return columns_from_root_table.values()

    def _add_sort_to_query(self, query):
        for sort in self._sort:
            query = query.order_by(sort)
        return query

    def _add_where_to_query(self, query):
        for where in self._where:
            query = query.where(where)
        for e_c in self._extras_conditions:
            query = query.where(e_c)
        return query

    def _do_subquery(self):
        # if embed with limit or offset requested then we will use a subquery
        # for the root table
        return self._embeds and (self._limit or self._offset)

    def _get_embed_list(self, embed_joins):
        valid_embed = embed_joins.keys()
        embed_list = []
        for embed_elem in self._embeds:
            left = embed_elem.split('.')[0]
            if embed_elem not in valid_embed:
                raise dci_exc.DCIException(
                    'Invalid embed list',
                    payload={'Valid elements': valid_embed}
                )
            if left not in embed_list:
                embed_list.append(left)
        return sorted(set(embed_list))

    def build(self):

        select_clause = self._get_root_columns()
        root_select = self._root_table
        if self._do_subquery():
            root_subquery = sql.select(select_clause)
            root_subquery = self._add_where_to_query(root_subquery)
            root_subquery = self._add_sort_to_query(root_subquery)
            if self._limit:
                root_subquery = root_subquery.limit(self._limit)
            if self._offset:
                root_subquery = root_subquery.offset(self._offset)
            root_subquery = root_subquery.alias(self._root_table.name)
            select_clause = [root_subquery]
            root_select = root_subquery

        embed_joins = embeds.EMBED_JOINS.get(self._root_table.name)(root_select)
        embed_list = self._get_embed_list(embed_joins)

        children = root_select
        for embed_elem in embed_list:
            for join_param in embed_joins[embed_elem]:
                children = children.join(**join_param)
            select_clause.append(embeds.EMBED_STRING_TO_OBJECT[embed_elem])

        query = sql.select(select_clause,
                           use_labels=True,
                           from_obj=children)

        if not self._do_subquery():
            query = self._add_sort_to_query(query)
            query = self._add_where_to_query(query)

            if self._limit:
                query = query.limit(self._limit)
            if self._offset:
                query = query.offset(self._offset)

        return query


def format_result(rows):
    return rows


def flask_headers_to_dict(headers):
    """Parse headers for finding dci related ones

    Replace each characters '-' from headers by '_' for sql backend
    """
    rv = {}
    for header, value in six.iteritems(dict(headers)):
        header = header.replace('-', '_').lower()
        if header.startswith('dci'):
            rv[header[4:]] = value

    return rv


def build_file_path(file_folder, team_id, file_id, create=True):
    directory = os.path.join(
        file_folder, team_id, file_id[0:2], file_id[2:4], file_id[4:6]
    )
    if create and not os.path.exists(directory):
        os.makedirs(directory)

    return os.path.join(directory, file_id)
