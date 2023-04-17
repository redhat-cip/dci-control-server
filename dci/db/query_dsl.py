# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Red Hat, Inc
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

import pyparsing as pp
from sqlalchemy import sql


_field = pp.Word(pp.alphanums + "_")
_value = pp.Word(pp.alphanums + "_" + "-" + " " + "%")
_comma = pp.Suppress(pp.Literal(","))
_lp = pp.Suppress(pp.Literal("("))
_rp = pp.Suppress(pp.Literal(")"))

_operations = {
    "contains",
    "not_contains",
    "lt",
    "le",
    "gt",
    "ge",
    "eq",
    "ne",
    "like",
    "ilike",
}
_operations = pp.oneOf(" ".join(_operations))
_op = _operations + _lp + _field + _comma + _value + _rp

_unary_operations = {"null"}
_unary_operations = pp.oneOf(" ".join(_unary_operations))
_uop = _unary_operations + _lp + _field + _rp

_comma_op = _comma + _op | _uop
_ops = pp.Group(_op | _uop) + pp.ZeroOrMore(pp.Group(_comma_op))

_logical_operations = {"and", "or", "not"}
_lbop = pp.oneOf(" ".join(_logical_operations))

query = pp.Forward()
query << (
    _ops
    | _lbop
    + _lp
    + (_ops | query)
    + pp.ZeroOrMore(_comma + (_ops | pp.Group(query)))
    + _rp
)


def parse(q):
    return query.parseString(q).asList()


def _build(sa_query, parsed_query, model_object):
    columns = model_object.__mapper__.columns.keys()
    if isinstance(parsed_query[0], list):
        parsed_query = parsed_query[0]
    op = parsed_query[0]
    operands = parsed_query[1:]

    if op in _logical_operations:
        sql_op = getattr(sql, op + "_")
        res = []
        for operand in operands:
            res.append(_build(sa_query, operand, model_object))
        return sql_op(*res)

    value = None
    if len(operands) >= 2:
        field, value = operands
    else:
        field = operands[0]

    if field not in columns:
        raise dci_exc.DCIException("Invalid field: %s" % field)
    m_column = getattr(model_object, field)

    res = None
    if op == "eq":
        res = m_column == value
    elif op == "ne":
        res = m_column != value
    elif op == "lt":
        res = m_column < value
    elif op == "le":
        res = m_column <= value
    elif op == "gt":
        res = m_column > value
    elif op == "ge":
        res = m_column >= value
    elif op == "contains":
        res = m_column.contains([value])
    elif op == "not_contains":
        res = not m_column.contains([value])
    elif op == "null":
        res = sql.or_(m_column.is_(None), m_column == "", m_column == "")
    elif op == "like":
        res = m_column.like(value)
    elif op == "ilike":
        res = m_column.ilike(value)
    else:
        raise dci_exc.DCIException("Invalid operation: %s" % op)
    return res


def build(sa_query, parsed_query, model_object):
    return sa_query.filter(_build(sa_query, parsed_query, model_object))
