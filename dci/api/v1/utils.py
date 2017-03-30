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
from dci.db import embeds

import collections
import os


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


class QueryBuilder2(object):

    def __init__(self, root_table, args, strings_to_columns, ignore_columns=None):  # noqa
        self._root_table = root_table
        self._embeds = args.get('embed', [])
        self._limit = args.get('limit', None)
        self._offset = args.get('offset', None)
        self._sort = sort_query(args.get('sort', []), strings_to_columns)
        self._where = where_query(args.get('where', []), self._root_table,
                                  strings_to_columns)
        self._strings_to_columns = strings_to_columns
        self._extras_conditions = []
        self._ignored_columns = ignore_columns or []

    def add_extra_condition(self, condition):
        self._extras_conditions.append(condition)

    def _get_root_columns(self):
        # remove ignored columns
        columns_from_root_table = dict(self._strings_to_columns)
        for column_to_ignore in self._ignored_columns:
            columns_from_root_table.pop(column_to_ignore, None)
        return list(columns_from_root_table.values())

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
            embed_list.append(embed_elem)
        return sorted(set(embed_list))

    def get_query(self):
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

        query = sql.select(select_clause, use_labels=True)
        if self._embeds:
            embed_joins = embeds.EMBED_JOINS.get(self._root_table.name)(root_select)  # noqa
            embed_list = self._get_embed_list(embed_joins)
            children = root_select
            embed_sorts = []
            for embed_elem in embed_list:
                for param in embed_joins[embed_elem]:
                    children = children.join(param['right'], param['onclause'],
                                             param.get('isouter', False))
                    if param.get('sort', None) is not None:
                        embed_sorts.append(param.get('sort'))
                select_elem = embeds.EMBED_STRING_TO_OBJECT[self._root_table.name][embed_elem]  # noqa
                if isinstance(select_elem, list):
                    select_clause.extend(select_elem)
                else:
                    select_clause.append(select_elem)
            query = sql.select(select_clause, use_labels=True, from_obj=children)  # noqa

            for embed_sort in embed_sorts:
                query = query.order_by(embed_sort)

        if not self._do_subquery():
            query = self._add_sort_to_query(query)
            query = self._add_where_to_query(query)

            if self._limit:
                query = query.limit(self._limit)
            if self._offset:
                query = query.offset(self._offset)

        return query

    def get_number_of_rows(self, root_table=None, where=None):
        if root_table is not None:
            query = sql.select([func.count(root_table.c.id)])
            query = query.where(where)
        else:
            query = sql.select([func.count(self._root_table.c.id)])
            query = self._add_where_to_query(query)
        return flask.g.db_conn.execute(query).scalar()

    def execute(self, fetchall=False, fetchone=False):
        if fetchall:
            return flask.g.db_conn.execute(self.get_query()).fetchall()
        elif fetchone:
            return flask.g.db_conn.execute(self.get_query()).fetchone()

    def _get_pg_query(self):
        from sqlalchemy.dialects import postgresql
        return str(self.get_query().compile(dialect=postgresql.dialect()))


def _format_level_1(rows, root_table_name):
    """
    Transform sqlalchemy source:
    [{'a_id' : 'id1',
      'a_name' : 'name1,
      'b_id' : 'id2',
      'b_name' : 'name2},
     {'a_id' : 'id3',
      'a_name' : 'name3,
      'b_id' : 'id4',
      'b_name' : 'name4}
    ]
    to
    [{'id' : 'id1',
      'name': 'name2',
      'b' : {'id': 'id2', 'name': 'name2'},
     {'id' : 'id3',
      'name': 'name3',
      'b' : {'id': 'id4', 'name': 'name4'}
    ]
    """
    result_rows = []
    for row in rows:
        row = dict(row)
        result_row = {}
        prefixes_to_remove = []
        for field in row:
            prefix, suffix = field.split('_', 1)
            if suffix == 'id' and row[field] is None:
                prefixes_to_remove.append(prefix)
            if prefix not in result_row:
                result_row[prefix] = {suffix: row[field]}
            else:
                result_row[prefix].update({suffix: row[field]})
        # remove field with id == null
        for prefix_to_remove in prefixes_to_remove:
            result_row.pop(prefix_to_remove)
        root_table_fields = result_row.pop(root_table_name)
        result_row.update(root_table_fields)
        result_rows.append(result_row)
    return result_rows


def _format_level_2(rows, list_embeds, embed_many):
    """
    From the _format_level_1 function we have a list of rows. Because of using
    joins, we have as many rows as join result.

    For example:
    [{'id' : 'id1',
      'name' : 'name1,
      'b' : {'id': 'id2,
             'name': 'name2'}
     }
     {'id' : 'id1',
      'name' : 'name1,
      'b' : {'id' : 'id4',
             'name' : 'name4}
     }
    ]

    Here there is two elements which correspond to one rows because of the
    embed field 'b'. So we should transform it to:

    [{'id' : 'id1',
      'name' : 'name1,
      'b' : [{'id': 'id2,
             'name': 'name2'},
             {'id' : 'id4',
             'name' : 'name4}]
     }
    ]

    This is the purpose of this function.
    """

    def _uniqify_list(list_of_dicts):
        # list() for py34
        result = []
        set_ids = set()
        for v in list_of_dicts:
            if v['id'] in set_ids:
                continue
            set_ids.add(v['id'])
            result.append(v)
        return result

    row_ids_to_embed_values = {}
    for row in rows:
        # for each row, associate rows's id -> {all embeds values}
        if row['id'] not in row_ids_to_embed_values:
            row_ids_to_embed_values[row['id']] = {}
        # add embeds values to the current row
        for embd in list_embeds:
            if embd not in row:
                continue
            if embd not in row_ids_to_embed_values[row['id']]:
                # create a list or a dict depending on embed_many
                if embed_many[embd]:
                    row_ids_to_embed_values[row['id']][embd] = [row[embd]]
                else:
                    row_ids_to_embed_values[row['id']][embd] = row[embd]
            else:
                if embed_many[embd]:
                    row_ids_to_embed_values[row['id']][embd].append(row[embd])
        # uniqify each embed list
        for embd in list_embeds:
            if embd in row_ids_to_embed_values[row['id']]:
                embed_values = row_ids_to_embed_values[row['id']][embd]
                if isinstance(embed_values, list):
                    row_ids_to_embed_values[row['id']][embd] = _uniqify_list(embed_values)  # noqa
            else:
                row_ids_to_embed_values[row['id']][embd] = {}
                if embed_many[embd]:
                    row_ids_to_embed_values[row['id']][embd] = []

    # last loop over the initial rows in order to keep the ordering
    result = []
    # if row id in seen set then it means the row has been completely processed
    seen = set()
    for row in rows:
        if row['id'] in seen:
            continue
        seen.add(row['id'])
        new_row = {}
        # adds level 1 fields
        for field in row:
            if field not in list_embeds:
                new_row[field] = row[field]
        # adds all level 2 fields
        # list() for py34
        row_ids_to_embed_values_keys = list(row_ids_to_embed_values[new_row['id']].keys())  # noqa
        row_ids_to_embed_values_keys.sort()
        # adds the nested fields if there is somes
        for embd in list_embeds:
            if embd in row_ids_to_embed_values_keys:
                if '.' in embd:
                    prefix, suffix = embd.split('.', 1)
                    new_row[prefix][suffix] = row_ids_to_embed_values[new_row['id']][embd]  # noqa
                else:
                    new_row[embd] = row_ids_to_embed_values[new_row['id']][embd]  # noqa
            else:
                new_row_embd_value = {}
                if embed_many[embd]:
                    new_row_embd_value = []
                if '.' in embd:
                    prefix, suffix = embd.split('.', 1)
                    new_row[prefix][suffix] = new_row_embd_value
                else:
                    new_row[embd] = new_row_embd_value
        # row is complete !
        result.append(new_row)
    return result


def format_result(rows, root_table_name, list_embeds, embed_many):
    result_rows = _format_level_1(rows, root_table_name)

    if list_embeds:
        return _format_level_2(result_rows, list_embeds, embed_many)
    return result_rows


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


def build_file_path(file_folder, team_id, file_id, create=True):
    team_id = str(team_id)
    file_id = str(file_id)
    directory = os.path.join(
        file_folder, team_id, file_id[0:2], file_id[2:4], file_id[4:6]
    )
    if create and not os.path.exists(directory):
        os.makedirs(directory)

    return os.path.join(directory, file_id)


def common_values_dict(user):
    """Build a basic values object used in every create method.

       All our resources contain a same subset of value. Instead of
       redoing this code everytime, this method ensures it is done only at
       one place.
    """

    created_at, updated_at = utils.get_dates(user)
    etag = utils.gen_etag()
    values = {
        'id': utils.gen_uuid(),
        'created_at': created_at,
        'updated_at': updated_at,
        'etag': etag
    }

    return values
