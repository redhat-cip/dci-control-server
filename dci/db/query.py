#
# Copyright (C) 2023 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

""" Query language for the where clause of the API.

Exemple: q(or(like(name,openshift%),in(tags,stage:ocp)))
"""

from sqlalchemy.types import ARRAY
from sqlalchemy import or_, not_


class SyntaxError(Exception):
    pass


def build(args, model, query, columns, do_filter=True):
    if isinstance(args, list) and "_" + args[0] in globals():
        return globals()["_" + args[0]](args[1:], model, query, columns, do_filter)
    else:
        raise SyntaxError("Invalid function %s" % args)


def parse(s):
    func = s.split("(", 1)
    if len(func) != 2:
        return s
    if len(func[1]) == 0 or not func[1][-1] == ")":
        raise SyntaxError("Invalid syntax %s" % s)
    args = split(func[1][:-1])
    return [func[0]] + [parse(a) for a in args]


def split(s):
    count = 0
    start = 0
    ret = []
    for idx in range(1, len(s)):
        if s[idx] == "(":
            count += 1
        elif s[idx] == ")":
            count -= 1
        elif count == 0 and s[idx] == ",":
            ret.append(s[start:idx])
            start = idx + 1
    ret.append(s[start : idx + 1])
    return ret


def left(args, model, columns):
    if isinstance(args, str):
        col = check_column(args, columns)
        return getattr(model, col)
    else:
        raise SyntaxError("Invalid column %s" % args)


def check_column(col, columns):
    if col in columns:
        return col
    raise SyntaxError("Invalid column name %s" % col)


def right(args):
    if isinstance(args, str):
        return args
    else:
        raise SyntaxError("Invalid value %s" % args[0])


def _q(args, model, query, columns, do_filter):
    if len(args) != 1:
        raise SyntaxError("invalid number of args %d for q" % len(args))
    return build(args[0], model, query, columns)


def _eq(args, model, query, columns, do_filter):
    if len(args) != 2:
        raise SyntaxError("invalid number of args %d for eq" % len(args))
    m_column = left(args[0], model, columns)
    val = right(args[1])
    if do_filter:
        return query.filter(m_column == val)
    else:
        return m_column == val


def _ne(args, model, query, columns, do_filter):
    if len(args) != 2:
        raise SyntaxError("invalid number of args %d for ne" % len(args))
    m_column = left(args[0], model, query, columns)
    val = right(args[1])
    if do_filter:
        return query.filter(m_column != val)
    else:
        return m_column != val


def _gt(args, model, query, columns, do_filter):
    if len(args) != 2:
        raise SyntaxError("invalid number of args %d for gt" % len(args))
    m_column = left(args[0], model, columns)
    val = right(args[1])
    if do_filter:
        return query.filter(m_column > val)
    else:
        return m_column > val


def _ge(args, model, query, columns, do_filter):
    if len(args) != 2:
        raise SyntaxError("invalid number of args %d for ge" % len(args))
    m_column = left(args[0], model, columns)
    val = right(args[1])
    if do_filter:
        return query.filter(m_column >= val)
    else:
        return m_column >= val


def _lt(args, model, query, columns, do_filter):
    if len(args) != 2:
        raise SyntaxError("invalid number of args %d for lt" % len(args))
    m_column = left(args[0], model, columns)
    val = right(args[1])
    if do_filter:
        return query.filter(m_column < val)
    else:
        return m_column < val


def _le(args, model, query, columns, do_filter):
    if len(args) != 2:
        raise SyntaxError("invalid number of args %d for le" % len(args))
    m_column = left(args[0], model, columns)
    val = right(args[1])
    if do_filter:
        return query.filter(m_column <= val)
    else:
        return m_column <= val


def _null(args, model, query, columns, do_filter):
    if len(args) != 1:
        raise SyntaxError("invalid number of args %d for null" % len(args))
    m_column = left(args[0], model, columns)
    if do_filter:
        return query.filter(m_column.is_(None))
    else:
        return m_column.is_(None)


def _like(args, model, query, columns, do_filter):
    if len(args) != 2:
        raise SyntaxError("invalid number of args %d for like" % len(args))
    m_column = left(args[0], model, columns)
    val = right(args[1])
    if do_filter:
        return query.filter(m_column.like(val))
    else:
        return m_column.like(val)


def _ilike(args, model, query, columns, do_filter):
    if len(args) != 2:
        raise SyntaxError("invalid number of args %d for ilike" % len(args))
    m_column = left(args[0], model, columns)
    val = right(args[1])
    if do_filter:
        return query.filter(m_column.ilike(val))
    else:
        return m_column.ilike(val)


def _contains(args, model, query, columns, do_filter):
    if len(args) < 2:
        raise SyntaxError("invalid number of args %d for contains" % len(args))
    m_column = left(args[0], model, columns)
    if isinstance(m_column.type, ARRAY):
        val = [right(a) for a in args[1:]]
        if do_filter:
            return query.filter(m_column.contains(val))
        else:
            return m_column.contains(val)
    raise SyntaxError("%s is not an array" % args[0])


def _not_contains(args, model, query, columns, do_filter):
    if len(args) < 2:
        raise SyntaxError("invalid number of args %d for not_contains" % len(args))
    m_column = left(args[0], model, columns)
    if isinstance(m_column.type, ARRAY):
        val = [right(a) for a in args[1:]]
        if do_filter:
            return query.filter(~m_column.contains(val))
        else:
            return ~m_column.contains(val)
    raise SyntaxError("%s is not an array" % args[0])


def _and(args, model, query, columns, do_filter):
    for a in args:
        query = build(a, model, query, columns, do_filter)
    return query


def _or(args, model, query, columns, do_filter):
    clauses = []
    for a in args:
        clauses.append(build(a, model, query, columns, False))
    return query.filter(or_(*clauses))


def _not(args, model, query, columns, do_filter):
    if len(args) != 1:
        raise SyntaxError("invalid number of args %d for not" % len(args))
    return query.filter(not_(build(args[0], model, query, columns, False)))


# query.py ends here
