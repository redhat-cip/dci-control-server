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

import datetime
import flask
from sqlalchemy import sql, func
import uuid
from OpenSSL import crypto

from dci.common import exceptions as dci_exc
from dci.common import utils
from dci.db import models
from dci.db import embeds


def createKeyPair(type=crypto.TYPE_RSA, bits=1024):
    """
    Create a public/private key pair.
    Arguments: type - Key type, must be one of TYPE_RSA and TYPE_DSA
               bits - Number of bits to use in the key
    Returns:   The public/private key pair in a PKey object
    """
    pkey = crypto.PKey()
    pkey.generate_key(type, bits)
    return pkey


def createCertRequest(pkey, digest="sha256"):
    """
    Create a certificate request.
    Arguments: pkey   - The key to associate with the request
               digest - Digestion method to use for signing, default is sha256
               **name - The name of the subject of the request, possible
                        arguments are:
                          C     - Country name
                          ST    - State or province name
                          L     - Locality name
                          O     - Organization name
                          OU    - Organizational unit name
                          CN    - Common name
                          emailAddress - E-mail address
    Returns:   The certificate request in an X509Req object
    """
    req = crypto.X509Req()

    req.get_subject().C = "FR"
    req.get_subject().ST = "IDF"
    req.get_subject().L = "Paris"
    req.get_subject().O = "RedHat"  # noqa
    req.get_subject().OU = "DCI"
    req.get_subject().CN = "DCI-remoteCI"

    req.set_pubkey(pkey)
    req.sign(pkey, digest)
    return req


def get_key_and_cert_signed(pkey_path, cert_path, digest="sha256"):
    key = createKeyPair()
    csr = createCertRequest(key)
    CAprivatekey = crypto.load_privatekey(crypto.FILETYPE_PEM,
                                          open(pkey_path, 'rb').read())
    caCert = crypto.load_certificate(crypto.FILETYPE_PEM,
                                     open(cert_path, 'rb').read())

    cert = crypto.X509()
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)
    cert.set_issuer(caCert.get_subject())
    cert.set_subject(csr.get_subject())
    cert.set_pubkey(csr.get_pubkey())
    cert.sign(CAprivatekey, digest)

    return key, cert


def verify_existence_and_get(id, table, name=None, get_id=False):
    """Verify the existence of a resource in the database and then
    return it if it exists, according to the condition, or raise an
    exception.

    :param id: id of the resource
    :param table: the table object
    :param name: the name of the row to look for
    :param get_id: if True, return only the ID
    :return:
    """

    where_clause = table.c.id == id
    if name:
        where_clause = table.c.name == name

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
    """Retrieve the list of topics IDs a user has access to."""

    if user.is_super_admin() or user.is_read_only_user() or user.is_epm():
        query = sql.select([models.TOPICS])
    else:
        query = (sql.select([models.JOINS_TOPICS_TEAMS.c.topic_id])
                 .select_from(
                     models.JOINS_TOPICS_TEAMS.join(
                         models.TOPICS, sql.and_(models.JOINS_TOPICS_TEAMS.c.topic_id == models.TOPICS.c.id,  # noqa
                                                 models.TOPICS.c.state == 'active'))  # noqa
                  ).where(
                      sql.or_(models.JOINS_TOPICS_TEAMS.c.team_id.in_(user.teams_ids),  # noqa
                              models.JOINS_TOPICS_TEAMS.c.team_id.in_(user.child_teams_ids))))  # noqa

    rows = flask.g.db_conn.execute(query).fetchall()
    return [str(row[0]) for row in rows]


def verify_team_in_topic(user, topic_id):
    """Verify that the user's team does belongs to the given topic. If
    the user is an admin or read only user then it belongs to all topics.
    """
    if user.is_super_admin() or user.is_read_only_user():
        return
    if str(topic_id) not in user_topic_ids(user):
        raise dci_exc.Unauthorized()


def get_columns_name_with_objects(table, table_prefix=False):
    if table_prefix:
        columns = {
            '%s_%s' % (table.name, column.name): getattr(table.columns, column.name)  # noqa
            for column in table.columns
        }
    else:
        columns = {
            column.name: getattr(table.columns, column.name)
            for column in table.columns
        }
    return columns


def sort_query(sort, root_valid_columns, embeds_valid_columns={}, default='-created_at'):  # noqa
    order_by = []
    if not sort and not root_valid_columns:
        return []
    if not sort:
        sort = [default]
    valid_columns_keys = list(root_valid_columns.keys())
    valid_columns = dict(root_valid_columns)
    if embeds_valid_columns:
        valid_columns.update(embeds_valid_columns)
        embed_valid_columns_keys = [i.replace('_', '.', 1)
                                    for i in list(embeds_valid_columns.keys())]
        valid_columns_keys.extend(embed_valid_columns_keys)
    for sort_elem in sort:
        sort_order = (sql.desc
                      if sort_elem.startswith('-') else sql.asc)
        sort_elem = sort_elem.strip(' -')
        if sort_elem not in valid_columns_keys:
            raise dci_exc.DCIException(
                'Invalid sort key: "%s"' % sort_elem,
                payload={'Valid sort keys': sorted(set(valid_columns_keys))}
            )
        if '.' in sort_elem:
            sort_elem = sort_elem.replace('.', '_', 1)
        order_by.append(sort_order(valid_columns[sort_elem]))
    return order_by


def add_sort_to_query(query, sort_list):
    for sort in sort_list:
        query = query.order_by(sort)
    return query


def where_query(where, table, columns):
    where_conds = []
    err_msg = 'Invalid where key: "%s"'

    def _get_column(table, columns, name):
        payload = {'error': 'where key must have the following form '
                            '"key:value"'}

        if '.' in name:
            subtable_name, name = name.split('.')
            table_obj = embeds.EMBED_STRING_TO_OBJECT[table.name]
            try:
                table = table_obj[subtable_name]
            except KeyError:
                payload = {'valid_keys': list(table_obj.keys())}
                raise dci_exc.DCIException(err_msg % name, payload=payload)
            columns = get_columns_name_with_objects(table)

        if name not in columns:
            payload = {'valid_keys': list(columns.keys())}
            raise dci_exc.DCIException(err_msg % name, payload=payload)
        return getattr(table.c, name)

    for where_elem in where:
        try:
            name, value = where_elem.split(':', 1)
        except ValueError:
            payload = {'error': 'where key must have the following form '
                                '"key:value"'}
            raise dci_exc.DCIException(err_msg % where_elem, payload=payload)

        m_column = _get_column(table, columns, name)
        # TODO(yassine): do the same for columns type different from string
        # if it's an Integer column, then try to cast the value
        try:
            if str(m_column.type) == "UUID" and uuid.UUID(value):
                pass
            elif m_column.type.python_type == int:
                value = int(value)
        except ValueError:
            payload = {name: '%s is not a %s' % (name, m_column.type)}
            raise dci_exc.DCIException(err_msg % name, payload=payload)

        where_conds.append(m_column == value)
    return where_conds


def add_where_to_query(query, where_list):
    for where in where_list:
        query = query.where(where)
    return query


def request_wants_html():
    best = (flask.request.accept_mimetypes
            .best_match(['text/html', 'application/json']))

    return (best == 'text/html' and
            flask.request.accept_mimetypes[best] >
            flask.request.accept_mimetypes['application/json'])


class QueryBuilder(object):

    def __init__(self, root_table, args={}, strings_to_columns={},
                 ignore_columns=None, root_join_table=None, root_join_condition=None):  # noqa
        self._root_table = root_table
        self._root_join_table = root_join_table
        self._root_join_condition = root_join_condition
        self._embeds = args.get('embed', [])
        self._limit = args.get('limit', None)
        self._offset = args.get('offset', None)
        self._sort = self._get_sort_query_with_embeds(args.get('sort', []),
                                                      root_table.name,
                                                      strings_to_columns)
        self._where = where_query(args.get('where', []), self._root_table,
                                  strings_to_columns)
        self._strings_to_columns = strings_to_columns
        self._extras_conditions = []
        self._ignored_columns = ignore_columns or []

    def _get_sort_query_with_embeds(self, args_sort, root_table_name, strings_to_columns):  # noqa
        # add embeds field for the sorting
        strings_to_columns_with_embeds = {}
        if root_table_name in embeds.EMBED_STRING_TO_OBJECT:
            for embed_elem in embeds.EMBED_STRING_TO_OBJECT[root_table_name].values():  # noqa
                if isinstance(embed_elem, list):
                    embed_str_to_objects = {'%s_%s' % (c.table.name, c.name): c for c in embed_elem}  # noqa
                    strings_to_columns_with_embeds.update(embed_str_to_objects)
                else:
                    strings_to_columns_with_embeds.update(
                        get_columns_name_with_objects(embed_elem, table_prefix=True))  # noqa
        return sort_query(args_sort, strings_to_columns, strings_to_columns_with_embeds)  # noqa

    def add_extra_condition(self, condition):
        self._extras_conditions.append(condition)

    def _filtered_root_columns(self):
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
                    'Invalid embed element %s' % embed_elem,
                    payload={'Valid elements': valid_embed}
                )
            if left not in embed_list:
                embed_list.append(left)
            embed_list.append(embed_elem)
        return sorted(set(embed_list))

    def get_query(self, use_labels=True):
        select_clause = [self._root_table]
        if self._ignored_columns:
            select_clause = self._filtered_root_columns()
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

        children = root_select
        if (self._root_join_table is not None) and (self._root_join_condition is not None):  # noqa
            children = root_select.join(self._root_join_table,
                                        self._root_join_condition)
            select_clause.append(self._root_join_table)

        query = sql.select(select_clause, use_labels=use_labels, from_obj=children)  # noqa
        if self._embeds:
            embed_joins = embeds.EMBED_JOINS.get(self._root_table.name)(root_select)  # noqa
            embed_list = self._get_embed_list(embed_joins)
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

        if self._embeds:
            for embed_sort in embed_sorts:
                query = query.order_by(embed_sort)

        if not self._do_subquery():
            query = self._add_where_to_query(query)

            if self._limit:
                query = query.limit(self._limit)
            if self._offset:
                query = query.offset(self._offset)
        query = self._add_sort_to_query(query)
        return query

    def get_number_of_rows(self, root_table=None, where=None):
        if root_table is not None:
            query = sql.select([func.count(root_table.c.id)])
            query = query.where(where)
        else:
            query = sql.select([func.count(self._root_table.c.id)])
            query = self._add_where_to_query(query)
        return flask.g.db_conn.execute(query).scalar()

    def execute(self, fetchall=False, fetchone=False, use_labels=True):
        """
        :param fetchall: get all rows
        :param fetchone:  get only one row
        :param use_labels: prefix row columns names by the table name
        :return:
        """
        query = self.get_query(use_labels=use_labels)
        if fetchall:
            return flask.g.db_conn.execute(query).fetchall()
        elif fetchone:
            return flask.g.db_conn.execute(query).fetchone()

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
            if field.startswith('next_topic'):
                prefix = 'next_topic'
                suffix = field[11:]
                if suffix == 'id_1':
                    suffix = 'id'
            else:
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


def format_result(rows, root_table_name, list_embeds=None, embed_many=None):
    result_rows = _format_level_1(rows, root_table_name)

    if list_embeds is not None and embed_many is not None:
        return _format_level_2(result_rows, list_embeds, embed_many)
    return result_rows


def common_values_dict():
    """Build a basic values object used in every create method.

       All our resources contain a same subset of value. Instead of
       redoing this code everytime, this method ensures it is done only at
       one place.
    """
    now = datetime.datetime.utcnow().isoformat()
    etag = utils.gen_etag()
    values = {
        'id': utils.gen_uuid(),
        'created_at': now,
        'updated_at': now,
        'etag': etag
    }

    return values
