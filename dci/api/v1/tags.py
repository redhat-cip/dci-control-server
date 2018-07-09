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
from dci.common import exceptions as dci_exc
from dci.db import models
from dci import decorators
from dci.api.v1 import api
from dci.common import schemas
import datetime
from dci.common import utils

_TABLE = models.TAGS


@api.route('/tags', methods=['POST'])
@decorators.login_required
@decorators.check_roles
def create_tag(user):
    """Create a tag."""

    values = {
        'id': utils.gen_uuid(),
        'created_at': datetime.datetime.utcnow().isoformat()
    }

# values = v1_utils.common_values_dict(user)
    values.update(schemas.tag.post(flask.request.json))

    with flask.g.db_conn.begin():
        where_clause = sql.and_(
            _TABLE.c.value == values['name'])
        query = sql.select([_TABLE.c.id]).where(where_clause)
        if flask.g.db_conn.execute(query).fetchone():
            raise dci_exc.DCIConflict('Tag already exists', values)

        # create the label/value row
        query = _TABLE.insert().values(**values)
        flask.g.db_conn.execute(query)

        result = json.dumps({'tag': values})
        return flask.Response(result, 201,
                              content_type='application/json')


@api.route('/tags/<tag_id>', methods=['DELETE'])
@decorators.login_required
@decorators.check_roles
def delete_tag(tag_id):
    """Delete a tag."""

    query = _TABLE.delete().where(_TABLE.c.id == tag_id).values(**values)
    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIConflict('Tag deletion conflict', id)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/tags/<tag_id>/components/<component_id>', methods=['POST'])
@decorators.login_required
@decorators.check_roles
def associate_tag_component(tag_id, component_id):
    """Associate a tag to a component."""

    query = table.insert().values(**values)
    flask.g.db_conn.execute(query)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/tags/<tag_id>/components/<component_id>', methods=['DELETE'])
@decorators.login_required
@decorators.check_roles
def associate_tag_component(tag_id, component_id):
    """Delete association between tag and a component."""
    where_clause = sql.and_(
        _TABLE.c.tag_id == tag_id,
        _TABLE.c.component_id == component_id
    )
    query = table.delete().where(where_clause).values(**values)
    flask.g.db_conn.execute(query)

    result = json.dumps({'tag': values})
    return flask.Response(None, 204, content_type='application/json')


def purge_tags(table):
    """Purge all tags in archived mode."""
