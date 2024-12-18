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

import pyparsing as pp

_field = pp.Word(pp.alphanums + "_" + ".")
_word = pp.Word(
    pp.alphanums
    + " "
    + "_"
    + "-"
    + "%"
    + "."
    + ":"
    + "\\"
    + "*"
    + "?"
    + "+"
    + "{"
    + "}"
    + "["
    + "]"
)
_value_with_quotes = pp.Suppress(pp.Literal("'")) + _word + pp.Suppress(pp.Literal("'"))
_value_without_quotes = _word
_value = _value_without_quotes | _value_with_quotes

_value_for_list = pp.Word(pp.alphanums + "_" + "." + "-" + ":" + " ")
_value_for_list_without_quotes = _value_for_list
_value_for_list_with_quotes = (
    pp.Suppress(pp.Literal("'")) + _value_for_list + pp.Suppress(pp.Literal("'"))
)
_value_for_list = _value_for_list_without_quotes | _value_for_list_with_quotes

_comma = pp.Suppress(pp.Literal(","))
_lp = pp.Suppress(pp.Literal("("))
_rp = pp.Suppress(pp.Literal(")"))

_lb = pp.Suppress(pp.Literal("["))
_rb = pp.Suppress(pp.Literal("]"))

_comma_value = _comma + _value_for_list
_list = _lb + _value_for_list + pp.ZeroOrMore(_comma_value) + _rb

_comparison_operators = {"=", "!=", "<=", "<", ">=", ">", "=~"}
_comparison_operators = pp.oneOf(" ".join(_comparison_operators))
_comparison = _field + _comparison_operators + _value

_membership_operators = {"not_in", "in"}
_membership_operators = pp.oneOf(" ".join(_membership_operators))
_membership_operation = _field + _membership_operators + pp.Group(_list)

_logical_operators = {"and", "or"}
_logical_operators = pp.oneOf(" ".join(_logical_operators))
_logical_operation = (
    pp.Group(_lp + (_comparison | _membership_operation) + _rp)
    + _logical_operators
    + pp.Group(_lp + (_comparison | _membership_operation) + _rp)
    | _lp + (_comparison | _membership_operation) + _rp
    | (_comparison | _membership_operation)
)

query = pp.Forward()
query << (
    (_lp + pp.Group(query) + _rp + pp.ZeroOrMore(_logical_operators + query))
    | _logical_operation
)


def parse(q):
    return query.parseString(q, parseAll=True).asList()


_op_to_es_op = {"<": "lt", "<=": "lte", ">": "gt", ">=": "gte"}


def _handle_comparison_operator(handle_nested, operator, operand_1, operand_2):
    if handle_nested and "." in operand_1:
        return {
            "nested": {
                "path": operand_1.split(".")[0],
                "query": {"range": {operand_1: {_op_to_es_op[operator]: operand_2}}},
            }
        }
    return {"range": {operand_1: {_op_to_es_op[operator]: operand_2}}}


def _generate_from_operators(parsed_query, handle_nested=False):
    operand_1 = parsed_query[0]
    operator = parsed_query[1]
    operand_2 = parsed_query[2]

    if operator == "=":
        if handle_nested and "." in operand_1:
            return {
                "nested": {
                    "path": operand_1.split(".")[0],
                    "query": {"term": {operand_1: operand_2}},
                }
            }
        return {"term": {operand_1: operand_2}}
    if operator in _op_to_es_op.keys():
        return _handle_comparison_operator(
            handle_nested, operator, operand_1, operand_2
        )
    elif operator == "=~":
        _regexp = {
            "regexp": {
                operand_1: {
                    "value": operand_2,
                    "flags": "ALL",
                    "case_insensitive": True,
                }
            }
        }
        if handle_nested and "." in operand_1:
            return {"nested": {"path": operand_1.split(".")[0], "query": _regexp}}
        return _regexp
    elif operator == "not_in":
        if handle_nested and "." in operand_1:
            return {
                "nested": {
                    "path": operand_1.split(".")[0],
                    "query": {"bool": {"must_not": {"terms": {operand_1: operand_2}}}},
                }
            }
        return {"bool": {"must_not": {"terms": {operand_1: operand_2}}}}
    elif operator == "in":
        if handle_nested and "." in operand_1:
            return {
                "nested": {
                    "path": operand_1.split(".")[0],
                    "query": {"terms": {operand_1: operand_2}},
                }
            }
        return {"terms": {operand_1: operand_2}}


def _split_on_or(parsed_query):
    before_or = []
    after_or = []
    for i in range(len(parsed_query)):
        if parsed_query[i] != "or":
            before_or.append(parsed_query[i])
        elif parsed_query[i] == "or":
            after_or = parsed_query[i + 1 :]
            break
    return before_or, after_or


def _get_logical_operands(parsed_query):
    operands = []
    for q in parsed_query:
        if q != "or" and q != "and":
            operands.append(q)
    return operands


def _is_nested_query(operands_1, operands_2=None):
    path = None
    if (
        isinstance(operands_1, list)
        and isinstance(operands_1[0], list)
        and isinstance(operands_1[0][0], str)
        and "." in operands_1[0][0]
    ):
        path = operands_1[0][0].split(".")[0]
    if path:
        for o in operands_1:
            if o[0].split(".")[0] != path:
                return None
        if operands_2:
            for o in operands_2:
                if o[0].split(".")[0] != path:
                    return None
    return path


def _generate_es_query(parsed_query, handle_nested=True):
    if isinstance(parsed_query[0], str):
        return _generate_from_operators(parsed_query, handle_nested)
    if len(parsed_query) == 1:
        return _generate_es_query(parsed_query[0], handle_nested)

    if "or" in parsed_query:
        left_operands, right_operands = _split_on_or(parsed_query)
        path = _is_nested_query(left_operands, right_operands)
        if path:
            return {
                "nested": {
                    "path": path,
                    "query": {
                        "bool": {
                            "should": [
                                _generate_es_query(left_operands, handle_nested=False)
                            ]
                            + [_generate_es_query(right_operands, handle_nested=False)],
                        }
                    },
                }
            }
        else:
            return {
                "bool": {
                    "should": [_generate_es_query(left_operands)]
                    + [_generate_es_query(right_operands)],
                }
            }
    else:
        operands = _get_logical_operands(parsed_query)
        path = _is_nested_query(operands)
        if path:
            return {
                "nested": {
                    "path": path,
                    "query": {
                        "bool": {
                            "filter": [
                                _generate_es_query(o, handle_nested=False)
                                for o in operands
                            ]
                        }
                    },
                }
            }
        else:
            return {"bool": {"filter": [_generate_es_query(o) for o in operands]}}


def build(query):
    parsed_query = parse(query)
    return _generate_es_query(parsed_query)
