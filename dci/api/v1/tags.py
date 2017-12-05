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


_TABLE = models.TAGS


def create_tag(user, job_id):
    """Create a tag information associated to a specific job."""
    v1_utils.verify_existence_and_get(job_id, models.JOBS)

    values = v1_utils.common_values_dict(user)
    values.update(schemas.tag.post(flask.request.json))

    values.update({
        'job_id': job_id
    })

    with flask.g.db_conn.begin():
        where_clause = sql.and_(
            _TABLE.c.name == values['name'],
            _TABLE.c.job_id == values['job_id'])
        query = sql.select([_TABLE.c.id]).where(where_clause)
        if flask.g.db_conn.execute(query).fetchone():
            raise dci_exc.DCIConflict('Tag already exists', values['name'])

        # create the label/value row
        query = _TABLE.insert().values(**values)
        flask.g.db_conn.execute(query)
        result = json.dumps({'tag': values})
        return flask.Response(result, 201,
                              headers={'ETag': values['etag']},
                              content_type='application/json')


def get_all_tags_from_job(job_id):
    """Get all tags from a specific job."""

    query = (sql.select([_TABLE])
             .where(_TABLE.c.job_id == job_id))

    rows = flask.g.db_conn.execute(query)

    res = flask.jsonify({'tags': rows,
                         '_tag': {'count': rows.rowcount}})
    res.status_code = 200
    return res


def get_tag_by_id(t_id):
    """Get specific tag by id."""

    query = sql.select([_TABLE]).where(_TABLE.c.id == t_id)

    rows = flask.g.db_conn.execute(query)

    res = flask.jsonify({'tag': rows,
                         '_tag': {'count': rows.rowcount}})
    res.status_code = 200
    return res


def put_tag(job_id, tag_id):
    """Modify a tag."""

    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    values = schemas.tag.put(flask.request.json)

    tag_retrieved = v1_utils.verify_existence_and_get(tag_id, _TABLE)

    if tag_retrieved['job_id'] != job_id:
        raise dci_exc.DCIException(
            "tag '%s' is not associated to job '%s'." % (tag_id, job_id))

    values['etag'] = utils.gen_etag()
    where_clause = sql.and_(
        _TABLE.c.etag == if_match_etag,
        _TABLE.c.id == tag_id
    )
    query = _TABLE.update().where(where_clause).values(**values)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict('Tag', tag_id)

    return flask.Response(None, 204, headers={'ETag': values['etag']},
                          content_type='application/json')


def delete_tag(job_id, tag_id):
    """Delete a tag from a specific job."""

    tag_retrieved = v1_utils.verify_existence_and_get(tag_id, _TABLE)

    if tag_retrieved['job_id'] != job_id:
        raise dci_exc.DCIDeleteConflict(
            "Tag '%s' is not associated to job '%s'." % (tag_id, job_id))

    query = _TABLE.delete().where(_TABLE.c.id == tag_id)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict('Tag deletion conflict', tag_id)

    return flask.Response(None, 204, content_type='application/json')
