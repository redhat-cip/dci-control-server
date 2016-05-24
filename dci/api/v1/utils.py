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

from dci.common import exceptions as dci_exc
from dci.common import utils
from dci.db import models

import collections
import os


Embed = collections.namedtuple('Embed', ['model', 'many'])


def embed(model, many=False):
    return Embed(model, many)


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
    return {
        column.name: getattr(table.c, column.name)
        for column in table.columns
    }


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
        self.sort = []
        self.where = []
        self.select = [table]
        self._join = []
        self.valid_embed = embed or {}

    def join(self, embed_list):
        """Given a select query on one table columns and a list of tables to
        join with, this function add to the query builder the needed selections
        and joins
        """

        def flatten_columns(prefix, embed):
            """This function provides different labels for column names
            when doing joins.
            i.e: we want to join table A to B but both have a name field,
            when retrieving the data and casting them to a dict, the name
            field from A will be erased by the one in B. To avoid that
            we provide a custom label for B.name which will be b_name.
            """
            result = []
            columns = embed.model.c
            for c_name in columns.keys():
                # Condition to avoid conflict when fetching the data because by
                # default there is the key 'prefix_id' when prefix is the table
                # name to join. This is also avoided in the case of a many join
                # as the id is not in
                if c_name != 'id' or embed.many:
                    prefixed_column = '%s_%s' % (prefix, c_name)
                    result.append(columns[c_name].label(prefixed_column))
            return result

        for embed in sorted(embed_list):
            if embed not in self.valid_embed:
                raise dci_exc.DCIException(
                    'Invalid embed list: "%s"' % embed_list,
                    payload={'Valid elements': list(self.valid_embed)}
                )
            e = self.valid_embed[embed]
            # flatten all tables for the SQL select
            self.select.extend(flatten_columns(embed, e))

            # order is important for the SQL join
            self._join.append(e.model)

    def parse_rows(self, embed_list, rows):
        aggregates = dict.fromkeys(
            [e for e in embed_list if self.valid_embed[e].many],
            collections.defaultdict(list)
        )
        parsed_rows = collections.OrderedDict()

        for row in rows:
            row = group_embedded_resources(embed_list, row)
            for aggr, aggr_dict in six.iteritems(aggregates):
                try:
                    obj = row.pop(aggr)
                    if any(v is not None for v in obj.values()):
                        aggr_dict[row['id']].append(obj)
                except KeyError:
                    pass
            parsed_rows[row['id']] = row

        for row_id, row in six.iteritems(parsed_rows):
            for aggr, aggr_dict in six.iteritems(aggregates):
                row[aggr] = aggr_dict[row_id]

        return list(parsed_rows.values())

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

        if self._join:
            query_from = self.table
            for join in self._join:
                query_from = query_from.outerjoin(join)
            query = query.select_from(query_from)

        return query

    def build_nb_row(self):
        query = sql.select([func.count(self.table.c.id)])
        for where in self.where:
            query = query.where(where)

        if self._join:
            query_join = self.table
            for join in self._join:
                query_join = query_join.outerjoin(join)

            query = query.select_from(query_join)

        return query


def flask_headers_to_dict(headers):
    """ Parse headers for finding dci related ones

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
