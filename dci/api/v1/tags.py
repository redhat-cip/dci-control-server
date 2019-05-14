# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2018 Red Hat, Inc
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
from sqlalchemy import exc as sa_exc
from sqlalchemy import sql

from dci.common import exceptions as dci_exc
from dci.db import models
from dci import decorators
from dci.api.v1 import api
from dci.common import schemas
from dci.common.schemas2 import check_json_is_valid, tag_schema
import datetime
from dci.common import utils
from dci.api.v1 import utils as v1_utils

_TABLE = models.TAGS
_T_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)


def add_tag_to_resource(values, join_resource_tags):
    """

    :param values: the dict must contain the id of the resource as specified
                   in the join_resource_tags table
    :param join_resource_tags: the association table between the resource
                               and the tag
    :return: a dict with both the tag name and the tag id
    """

    values = dict(values)
    values.update(schemas.tag.post(flask.request.json))
    tag_name = values.pop('name')

    try:
        tag_id = v1_utils.verify_existence_and_get(None,
                                                   models.TAGS,
                                                   name=tag_name,
                                                   get_id=True)
    except dci_exc.DCIException:
        tag_id = utils.gen_uuid()
        flask.g.db_conn.execute(models.TAGS.insert().values(
            id=tag_id,
            name=tag_name))
    values['tag_id'] = tag_id
    query = join_resource_tags.insert().values(values)

    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict('tag', tag_name)

    return {'tag': {'id': tag_id, 'name': tag_name}}


@api.route('/tags', methods=['POST'])
@decorators.login_required
def create_tags(user):
    check_json_is_valid(tag_schema, flask.request.json)
    values = {
        'id': utils.gen_uuid(),
        'created_at': datetime.datetime.utcnow().isoformat()
    }
    values.update(flask.request.json)
    with flask.g.db_conn.begin():
        where_clause = sql.and_(
            _TABLE.c.name == values['name'])
        query = sql.select([_TABLE.c.id]).where(where_clause)
        if flask.g.db_conn.execute(query).fetchone():
            raise dci_exc.DCIConflict('Tag already exists', values)

        # create the label/value row
        query = _TABLE.insert().values(**values)
        flask.g.db_conn.execute(query)

        result = json.dumps({'tag': values})
        return flask.Response(result, 201,
                              content_type='application/json')


@api.route('/tags', methods=['GET'])
@decorators.login_required
def get_tags(user):
    """Get all tags."""
    args = schemas.args(flask.request.args.to_dict())
    query = v1_utils.QueryBuilder(_TABLE, args, _T_COLUMNS)
    nb_rows = query.get_number_of_rows()
    rows = query.execute(fetchall=True)
    rows = v1_utils.format_result(rows, _TABLE.name)
    return flask.jsonify({'tags': rows, '_meta': {'count': nb_rows}})


@api.route('/tags/<uuid:tag_id>', methods=['DELETE'])
@decorators.login_required
def delete_tag_by_id(user, tag_id):
    """Delete a tag."""
    query = _TABLE.delete().where(_TABLE.c.id == tag_id)
    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict('Tag deletion conflict', tag_id)

    return flask.Response(None, 204, content_type='application/json')
