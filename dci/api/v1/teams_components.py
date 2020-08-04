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

import flask
from flask import json
import logging
from sqlalchemy import exc as sa_exc
from sqlalchemy import sql

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import utils as v1_utils
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common.schemas import (
    check_json_is_valid,
    create_team_component_schema,
    update_team_component_schema,
    check_and_get_args
)
from dci.common import utils
from dci.db import embeds
from dci.db import models

# associate column names with the corresponding SA Column object
_TABLE = models.COMPONENTS
_TABLE_TAGS = models.JOIN_COMPONENTS_TAGS

_TABLE_TAGS_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE_TAGS)
_JJC = models.JOIN_JOBS_COMPONENTS
_VALID_EMBED = embeds.components()
_C_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)
_CF_COLUMNS = v1_utils.get_columns_name_with_objects(models.COMPONENTFILES)
_JOBS_C_COLUMNS = v1_utils.get_columns_name_with_objects(models.JOBS)
_EMBED_MANY = {
    'files': True,
    'jobs': True
}

logger = logging.getLogger(__name__)


@api.route('/teams/<uuid:team_id>/components', methods=['POST'])
@decorators.login_required
def create_team_component(user, team_id):
    values = flask.request.json
    check_json_is_valid(create_team_component_schema, values)
    values.update(v1_utils.common_values_dict())

    if user.is_not_in_team(team_id):
        raise dci_exc.Unauthorized()

    values['team_id'] = team_id
    query = _TABLE.insert().values(**values)

    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(_TABLE.name, 'name')

    result = json.dumps({'component': values})
    return flask.Response(result, 201, content_type='application/json')


@api.route('/teams/<uuid:team_id>/components/<uuid:c_id>', methods=['GET'])
@decorators.login_required
def get_team_component_by_id(user, team_id, c_id):
    if user.is_not_in_team(team_id):
        raise dci_exc.Unauthorized()
    component = v1_utils.verify_existence_and_get(c_id, _TABLE)
    if component['team_id'] != team_id:
        raise dci_exc.Unauthorized()

    return base.get_resource_by_id(user, component, _TABLE, _EMBED_MANY)


@api.route('/teams/<uuid:team_id>/components', methods=['GET'])
@decorators.login_required
def get_all_teams_components(user, team_id):
    """Get all components of a team."""
    if user.is_not_in_team(team_id):
        raise dci_exc.Unauthorized()

    args = check_and_get_args(flask.request.args.to_dict())

    query = v1_utils.QueryBuilder(_TABLE, args, _C_COLUMNS)

    query.add_extra_condition(sql.and_(
        _TABLE.c.team_id == team_id,
        _TABLE.c.state != 'archived'))

    nb_rows = query.get_number_of_rows()
    rows = query.execute(fetchall=True)
    rows = v1_utils.format_result(rows, _TABLE.name, args['embed'],
                                  _EMBED_MANY)

    return flask.jsonify({'components': rows, '_meta': {'count': nb_rows}})


@api.route('/teams/<uuid:team_id>/components/<uuid:c_id>', methods=['PUT'])
@decorators.login_required
def update_teams_components(user, team_id, c_id):
    if user.is_not_in_team(team_id):
        raise dci_exc.Unauthorized()
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    values = flask.request.json
    check_json_is_valid(update_team_component_schema, values)
    values['etag'] = utils.gen_etag()

    where_clause = sql.and_(
        _TABLE.c.etag == if_match_etag,
        _TABLE.c.id == c_id
    )

    query = _TABLE.update().returning(*_TABLE.columns).where(where_clause).\
        values(**values)

    result = flask.g.db_conn.execute(query)
    if not result.rowcount:
        raise dci_exc.DCIConflict('Component', c_id)

    return flask.Response(
        json.dumps({'component': result.fetchone()}), 200,
        headers={'ETag': values['etag']}, content_type='application/json'
    )


@api.route('/teams/<uuid:team_id>/components/<uuid:c_id>', methods=['DELETE'])
@decorators.login_required
def delete_team_component_by_id(user, team_id, c_id):
    if user.is_not_in_team(team_id):
        raise dci_exc.Unauthorized()
    component = v1_utils.verify_existence_and_get(c_id, _TABLE)
    if component['team_id'] != team_id:
        raise dci_exc.Unauthorized()

    values = {'state': 'archived'}
    where_clause = sql.and_(
        _TABLE.c.id == c_id
    )
    query = _TABLE.update().where(where_clause).values(**values)

    result = flask.g.db_conn.execute(query)

    if not result.rowcount:
        raise dci_exc.DCIDeleteConflict('Component', c_id)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/teams/<uuid:team_id>/components/<uuid:c_id>/tags', methods=['POST'])
@decorators.login_required
def add_tag_to_team_component(user, team_id, c_id):
    """Add a tag on a specific team component."""

    if user.is_not_in_team(team_id):
        raise dci_exc.Unauthorized()

    component = v1_utils.verify_existence_and_get(c_id, _TABLE)

    if component['team_id'] != team_id:
        raise dci_exc.Unauthorized()

    cmpt_values = {}
    cmpt_values['etag'] = utils.gen_etag()
    tag_name = flask.request.json.get('name')
    if tag_name and tag_name not in component['tags']:
        tag_name = [tag_name]
        cmpt_values['tags'] = component['tags'] + tag_name
        query = _TABLE.update().\
            where(_TABLE.c.id == c_id).\
            values(**cmpt_values)

        result = flask.g.db_conn.execute(query)
        if not result.rowcount:
            raise dci_exc.DCIConflict('teams_components', c_id)

    return flask.Response(None, 201, content_type='application/json')


@api.route('/teams/<uuid:team_id>/components/<uuid:c_id>/tags', methods=['DELETE'])
@decorators.login_required
def delete_tag_from_team_component(user, team_id, c_id):
    """Delete a tag from a specific team component."""

    component = v1_utils.verify_existence_and_get(c_id, _TABLE)
    cmpt_values = {}
    cmpt_values['etag'] = utils.gen_etag()
    tag_name = flask.request.json.get('name')
    tag_name = [tag_name] if tag_name else []
    cmpt_values['tags'] = list(set(component['tags']) - set(tag_name))
    query = _TABLE.update().\
        where(_TABLE.c.id == c_id).\
        values(**cmpt_values)

    result = flask.g.db_conn.execute(query)
    if not result.rowcount:
        raise dci_exc.DCIConflict('teams_components', c_id)

    return flask.Response(None, 204, content_type='application/json')
