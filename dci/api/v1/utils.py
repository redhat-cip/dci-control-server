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
    return [str(row[0]) for row in rows]


def verify_team_in_topic(user, topic_id):
    """Verify that the user's team does belongs to the given topic. If
    the user is an admin then it belongs to all topics.
    """
    if auth.is_admin(user):
        return
    if str(topic_id) not in user_topic_ids(user):
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
        if str(m_column.type) == "UUID":
            pass
        elif m_column.type.python_type == int:
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

    def __init__(self, table, offset=None, limit=None, embed=None):
        self.table = table
        self.offset = offset
        self.limit = limit
        self._sort = []
        self.sort = []
        self.where = []
        self.select = [table]
        self.extra_tables = []
        self.extra_where = []
        self._join = []
        self.valid_embed = embed or {}
        self.embed_list = []

    def ignore_columns(self, columns):
        """Remove the specified set of columns from the SQL query."""

        select = []
        for entity in self.select:
            if isinstance(entity, sa_Table):
                for column in entity._columns.values():
                    if column.name not in columns:
                        select.append(column)
            elif entity.name not in columns:
                select.append(entity)
        self.select = select

    def join(self, embed_list):
        """Given a select query on one table columns and a list of tables to
        join with, this function add to the query builder the needed selections
        and joins
        """

        for i in embed_list:
            root = i.split('.')[0]
            if root not in embed_list:
                embed_list.append(root)
        self.embed_list = sorted(set(embed_list))

        for embed in self.embed_list:
            if embed not in self.valid_embed:
                raise dci_exc.DCIException(
                    'Invalid embed list: "%s"' % embed_list,
                    payload={'Valid elements': list(self.valid_embed)}
                )
            e = self.valid_embed[embed]
            if not e:
                continue
            # order is important for the SQL join
            if e.join is not None:
                self._join.append(e.join)
            if e.where is not None:
                self.extra_where.append(e.where)
            if e.sort is not None:
                self._sort.append(e.sort)
            if e.select is not None:
                self.select += e.select

    def _remove_cur_table_field_prefix(self, row):
        t_row = collections.OrderedDict()
        t_prefix = self.table.name + '_'
        for i, v in row.items():
            if i.startswith(t_prefix):
                i = i[len(t_prefix):]
            t_row[i] = v
        return t_row

    def _flatten_embedded_field(self, row):
        # Rename the embedded fields from table_field to table.field to be
        # consistent with the internal model
        fixed_row = {}
        for e in self.embed_list:
            for k in row.keys():
                if k.startswith(e + '_'):
                    fixed_k = e + '.' + k[len(e) + 1:]
                    fixed_row[fixed_k] = row.pop(k)
        row.update(fixed_row)
        return row

    def dedup_rows(self, rows):
        # the DB returns a list of rows with all the information,
        # sometime, we will get several raws for on item. e.g: a
        # component has 3 associated jobs
        # This function, will loop over all the rows and generate
        # a Python structure:
        #
        # | remotecis.name | jobs.name |
        # ------------------------------
        # | r1             | job1      |
        # | r1             | job2      |
        # | r1             | job3      |
        #
        # => {"remotecis": {
        #     "name": "r1":
        #     "jobs": [
        #         {"name": "job1"},
        #         {"name": "job2"},
        #         {"name": "job3"}]}
        aggregates = [
            (e, collections.defaultdict(list), e.split('.'))
            for e in self.embed_list
            if self.valid_embed[e] and self.valid_embed[e].many]
        parsed_rows = collections.OrderedDict()

        for row in rows:
            row = self._remove_cur_table_field_prefix(row)
            row = self._flatten_embedded_field(row)
            row = group_embedded_resources(self.embed_list, row)
            for aggr, aggr_dict, aggr_splitted in aggregates:
                base_element = row
                for i in aggr_splitted[:-1]:
                    base_element = base_element[i]
                obj = base_element.pop(aggr_splitted[-1])
                if not obj.get('id'):
                    # skip the the object if ID is NULL
                    continue
                cur_ids = [i['id'] for i in aggr_dict[row['id']]]
                if obj['id'] not in cur_ids:
                    aggr_dict[row['id']].append(obj)
            parsed_rows[row['id']] = row

        for row_id, row in six.iteritems(parsed_rows):
            for aggr, aggr_dict, aggr_splitted in aggregates:
                base_element = row
                for i in aggr_splitted[:-1]:
                    base_element = base_element[i]
                if base_element:
                    base_element[aggr_splitted[-1]] = aggr_dict[row_id]

        return list(parsed_rows.values())

    def _get_ids(self):
        rows = flask.g.db_conn.execute(self.build_list_ids()).fetchall()
        return [i[0] for i in rows]

    def prepare_join(self, query):
        for join in self._join:
            query = query.select_from(join)
        for i in self.extra_tables:
            query.append_from(i)
        if self.extra_where:
            query = query.where(sql.and_(*self.extra_where))
        return query

    def build(self):
        distinct_on = [self.table.c.id] + [i + '_id' for i in self.embed_list]
        query = sql.select(self.select, use_labels=True).distinct(*distinct_on)
        # One record information may be splitted on more than just one SQL
        # row. These rows will be ultimately merged in one line by
        # dedup_rows().
        #
        # E.g:
        #
        #  | id   | embeded_field
        #  | id_1 |         data1
        #  | id_1 |         data2
        #
        # If we use a limit operator here, we may end up with a truncated
        # record. This is the reason why we do a first iteration to only
        # identify the IDs. The second iterations is used to actually collect
        # the full record data.
        ids = self._get_ids()
        if ids:
            _where = self.table.c.id.in_(ids)
        else:
            _where = self.table.c.id == None  # noqa
        self.extra_where.append(_where)

        for sort in distinct_on:
            query = query.order_by(sort)

        query = self.prepare_join(query).alias(str(self.table))
        query = sql.select(['*'], from_obj=query)
        try:  # case where a table is in the select
            id_c_name = '%s_%s' % (
                self.select[0].name, self.select[0].c['id'].name)
        except AttributeError:
            id_c_name = self.select[0].name
            if '_' not in id_c_name:
                id_c_name = str(self.table) + '_' + id_c_name
        for id_ in reversed(ids):
            query = query.order_by(text("%s='%s' ASC" % (id_c_name, id_)))
        return query

    def build_list_ids(self):
        # If we want the WHERE to work, we need to have its columns in the
        # SELECT
        search_columns = [s.element if hasattr(s, 'element') else s
                          for s in self.sort]
        query = sql.select([func.distinct(self.table.c.id)] + search_columns)

        for where in self.where:
            query = query.where(where)

        if self.limit:
            query = query.limit(self.limit)

        if self.offset:
            query = query.offset(self.offset)

        for sort in self.sort:
            query = query.order_by(sort)

        query = self.prepare_join(query)
        return query

    def build_nb_row(self):
        query = sql.select([
            func.count(
                func.distinct(self.table.c.id))]).select_from(self.table)

        for where in self.where:
            query = query.where(where)

        query = self.prepare_join(query)
        return query


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
