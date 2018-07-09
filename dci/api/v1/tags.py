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

from flask import json
from sqlalchemy import sql
from dci.api.v1 import utils as v1_utils
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import models


def create_tag(table, object_id, value):
    """Create a tag associated to a specific object."""
    v1_utils.verify_existence_and_get(object_id, table)

    values.update(schemas.tags.post(flask.request.json))

    with flask.g.db_conn.begin():
        where_clause = sql.and_(
            table.c.value == values['value'],
            table.c.id == values['id'])
        query = sql.select([table.c.id]).where(where_clause)
        if flask.g.db_conn.execute(query).fetchone():
            raise dci_exc.DCIConflict('Tag already exists', values['value'])

        # create the label/value row
        query = _TABLE.insert().values(**values)
        flask.g.db_conn.execute(query)
        result = json.dumps({'tag': values})
        return flask.Response(result, 201,
                              headers={'ETag': values['etag']},
                              content_type='application/json')


def get_all_tags_from_object(table, object_id):
    """Get all tags from a specific object."""

    query = (sql.select([table])
             .where(table.c.id == object_id))

    rows = flask.g.db_conn.execute(query)

    res = flask.jsonify({'tags': rows,
                         '_meta': {'count': rows.rowcount}})
    res.status_code = 200
    return res


def delete_tag(table, object_id):
    """Delete a tag from a specific object."""

    meta_retrieved = v1_utils.verify_existence_and_get(meta_id, _TABLE)

    if meta_retrieved['job_id'] != job_id:
        raise dci_exc.DCIDeleteConflict(
            "Meta '%s' is not associated to job '%s'." % (meta_id, job_id))

    query = _TABLE.delete().where(_TABLE.c.id == meta_id)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict('Tag deletion conflict', id)

    return flask.Response(None, 204, content_type='application/json')
