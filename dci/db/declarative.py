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

import datetime
from dci.common import exceptions as dci_exc
from dci.common import utils

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


class Mixin(object):
    id = sa.Column(pg.UUID(as_uuid=True),
                   primary_key=True,
                   default=utils.gen_uuid)
    created_at = sa.Column(sa.DateTime(),
                           default=datetime.datetime.utcnow,
                           nullable=False)
    updated_at = sa.Column(sa.DateTime(),
                           onupdate=datetime.datetime.utcnow,
                           default=datetime.datetime.utcnow,
                           nullable=False)
    etag = sa.Column(sa.String(40),
                     nullable=False,
                     default=utils.gen_etag,
                     onupdate=utils.gen_etag)

    def serialize(self, ignore_columns=[]):
        def _get_nested_columns():
            _res = {}
            for ic in ignore_columns:
                if '.' in ic:
                    k, v = ic.split('.')
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
            attr_obj = getattr(self, attr)
            if isinstance(attr_obj, list):
                _dict[attr] = []
                for ao in attr_obj:
                    _ignore_columns = []
                    if attr in nested_ignore_columns:
                        _ignore_columns = nested_ignore_columns[attr]
                    _dict[attr].append(ao.serialize(ignore_columns=_ignore_columns))
            else:
                if not attr.startswith('_') and attr not in ignore_columns:
                    _dict[attr] = self.__dict__[attr]
        return _dict


def handle_limitations(query, args):
    if args.get('limit'):
        query = query.limit(args.get('limit', 20))
    if args.get('offset'):
        query = query.offset(args.get('offset', 0))
    return query


def handle_args(query, model_object, args, limitations=True):
    if args.get('sort'):
        columns = model_object.__mapper__.columns.keys()
        for s in args.get('sort'):
            asc = True
            if s.startswith('-'):
                s = s[1:]
                asc = False
            if s not in columns:
                raise dci_exc.DCIException('Invalid sort key: "%s"' % s,
                                           payload={'Valid sort keys': sorted(set(columns))})
            if asc:
                query = query.order_by(getattr(model_object, s).asc())
            else:
                query = query.order_by(getattr(model_object, s).desc())
    if args.get('where'):
        columns = model_object.__mapper__.columns.keys()
        for w in args.get('where'):
            try:
                name, value = w.split(':', 1)
                if name not in columns:
                    raise dci_exc.DCIException('Invalid where key: "%s"' % w,
                                               payload={'Valid where keys': sorted(set(columns))})
            except ValueError:
                payload = {'error': 'where key must have the following form "key:value"'}
                raise dci_exc.DCIException('Invalid where key: "%s"' % w, payload=payload)
            query = query.filter(getattr(model_object, name) == value)
    if limitations:
        if args.get('limit'):
            query = query.limit(args.get('limit', 20))
        if args.get('offset'):
            query = query.offset(args.get('offset', 0))
    return query
