# -*- coding: utf-8 -*-
#
# Copyright (C) Red Hat, Inc
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

from dci.common import exceptions as dci_exc
from dci.db import query_dsl

import pyparsing as pp
from sqlalchemy import func, String
from sqlalchemy.types import ARRAY
from sqlalchemy.sql.expression import cast
import datetime
import uuid


class Mixin(object):
    def serialize(self, ignore_columns=[]):
        def _get_nested_columns():
            _res = {}
            for ic in ignore_columns:
                if "." in ic:
                    k, v = ic.split(".")
                    if k not in _res:
                        _res[k] = [v]
                    else:
                        _res[k].append(v)
            return _res

        nested_ignore_columns = []
        if ignore_columns:
            nested_ignore_columns = _get_nested_columns()
        _dict = {}
        _attrs = self.__dict__.keys()

        for attr in _attrs:
            if attr in ignore_columns:
                continue
            attr_obj = getattr(self, attr)
            if isinstance(attr_obj, list):
                _dict[attr] = []
                for ao in attr_obj:
                    _ignore_columns = []
                    if attr in nested_ignore_columns:
                        _ignore_columns = nested_ignore_columns[attr]
                    if isinstance(ao, Mixin):
                        _dict[attr].append(ao.serialize(ignore_columns=_ignore_columns))
                    else:
                        _dict[attr].append(ao)
            elif isinstance(attr_obj, Mixin):
                _ignore_columns = []
                if attr in nested_ignore_columns:
                    _ignore_columns = nested_ignore_columns[attr]
                _dict[attr] = attr_obj.serialize(ignore_columns=_ignore_columns)
            elif isinstance(attr_obj, uuid.UUID):
                _dict[attr] = str(attr_obj)
            elif isinstance(attr_obj, datetime.datetime):
                _dict[attr] = attr_obj.isoformat()
            elif not attr.startswith("_"):
                _dict[attr] = self.__dict__[attr]
        return _dict


def handle_pagination(query, args):
    limit_max = 200
    default_limit = 20
    default_offset = 0
    query = query.offset(args.get("offset", default_offset))
    query = query.limit(min(args.get("limit", default_limit), limit_max))
    return query


def handle_args(query, model_object, args):
    if args.get("sort"):
        columns = model_object.__mapper__.columns.keys()
        for s in args.get("sort"):
            asc = True
            if s.startswith("-"):
                s = s[1:]
                asc = False
            if s not in columns:
                raise dci_exc.DCIException(
                    'Invalid sort key: "%s"' % s,
                    payload={"Valid sort keys": sorted(set(columns))},
                )
            if asc:
                query = query.order_by(getattr(model_object, s).asc())
            else:
                query = query.order_by(getattr(model_object, s).desc())
    else:
        query = query.order_by(getattr(model_object, "created_at").desc())
    where = args.get("where")
    if where:
        columns = model_object.__mapper__.columns.keys()
        for w in where:
            try:
                name, value = w.split(":", 1)
                if not value:
                    value = None
            except ValueError:
                raise dci_exc.DCIException(
                    'Invalid where key: "%s"' % w,
                    payload={
                        "error": 'where key must have the following form "key:value"'
                    },
                )

            if name not in columns:
                raise dci_exc.DCIException(
                    'Invalid where key: "%s"' % w,
                    payload={"Valid where keys": sorted(set(columns))},
                )

            forbidden_column_names = [
                "api_secret",
                "data",
                "password",
                "cert_fp",
            ]
            if name in forbidden_column_names:
                raise dci_exc.DCIException('Invalid where key: "%s"' % name)

            m_column = getattr(model_object, name)
            if value is None:
                query = query.filter(m_column == value)
            elif isinstance(m_column.type, String):
                value = value.lower()
                m_column = func.lower(cast(m_column, String))
                if value.endswith("*") and value.count("*") == 1:
                    query = query.filter(m_column.contains(value.replace("*", "")))
                else:
                    query = query.filter(m_column == value)
            elif isinstance(m_column.type, ARRAY):
                query = query.filter(m_column.contains([value]))
            else:
                query = query.filter(m_column == value)
    elif args.get("query"):
        try:
            parsed_query = query_dsl.parse(args.get("query"))
            query = query_dsl.build(query, parsed_query, model_object)
        except pp.ParseException as pe:
            raise dci_exc.DCIException("error while parsing the query %s" % str(pe))
    if args.get("created_after"):
        query = query.filter(
            getattr(model_object, "created_at") >= args.get("created_after")
        )
    if args.get("updated_after"):
        query = query.filter(
            getattr(model_object, "updated_at") >= args.get("updated_after")
        )
    return query
