# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2017 Red Hat, Inc
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

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import remotecis
from dci.api.v1 import tests
from dci.api.v1 import utils as v1_utils
from dci import decorators
from dci.common import audits
from dci.common import exceptions as dci_exc
from dci.common.schemas import (
    check_json_is_valid,
    create_team_schema,
    update_team_schema,
    check_and_get_args
)
from dci.common import utils
from dci.db import embeds
from dci.db import models

# associate column names with the corresponding SA Column object
_TABLE = models.TEAMS
_VALID_EMBED = embeds.teams()
_T_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)
_EMBED_MANY = {
    'remotecis': True,
    'topics': True
}


@api.route('/teams', methods=['POST'])
@decorators.login_required
@audits.log
def create_teams(user):
    values = flask.request.json
    check_json_is_valid(create_team_schema, values)
    values.update(v1_utils.common_values_dict())

    if user.is_not_super_admin() and user.is_not_epm():
        raise dci_exc.Unauthorized()

    query = _TABLE.insert().values(**values)

    try:
        flask.g.db_conn.execute(query)
    except sa_exc.IntegrityError:
        raise dci_exc.DCICreationConflict(_TABLE.name, 'name')

    return flask.Response(
        json.dumps({'team': values}), 201,
        headers={'ETag': values['etag']}, content_type='application/json'
    )


@api.route('/teams', methods=['GET'])
@decorators.login_required
def get_all_teams(user):
    args = check_and_get_args(flask.request.args.to_dict())

    query = v1_utils.QueryBuilder(_TABLE, args, _T_COLUMNS)

    if user.is_not_super_admin() and user.is_not_epm() and user.is_not_read_only_user():
        query.add_extra_condition(_TABLE.c.id.in_(user.teams_ids))

    query.add_extra_condition(_TABLE.c.state != 'archived')

    nb_rows = query.get_number_of_rows()
    rows = query.execute(fetchall=True)
    rows = v1_utils.format_result(rows, _TABLE.name, args['embed'],
                                  _EMBED_MANY)

    return flask.jsonify({'teams': rows, '_meta': {'count': nb_rows}})


@api.route('/teams/<uuid:t_id>', methods=['GET'])
@decorators.login_required
def get_team_by_id(user, t_id):
    team = v1_utils.verify_existence_and_get(t_id, _TABLE)
    if user.is_not_in_team(t_id) and user.is_not_epm():
        raise dci_exc.Unauthorized()
    return base.get_resource_by_id(user, team, _TABLE, _EMBED_MANY)


@api.route('/teams/<uuid:team_id>/remotecis', methods=['GET'])
@decorators.login_required
def get_remotecis_by_team(user, team_id):
    if user.is_not_in_team(team_id) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    team = v1_utils.verify_existence_and_get(team_id, _TABLE)
    return remotecis.get_all_remotecis(team['id'])


@api.route('/teams/<uuid:team_id>/tests', methods=['GET'])
@decorators.login_required
def get_tests_by_team(user, team_id):
    if user.is_in_team(team_id) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    team = v1_utils.verify_existence_and_get(team_id, _TABLE)
    return tests.get_all_tests_by_team(user, team['id'])


@api.route('/teams/<uuid:t_id>', methods=['PUT'])
@decorators.login_required
def put_team(user, t_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    values = flask.request.json
    check_json_is_valid(update_team_schema, values)
    if user.is_not_super_admin() and user.is_not_epm():
        raise dci_exc.Unauthorized()

    v1_utils.verify_existence_and_get(t_id, _TABLE)

    values['etag'] = utils.gen_etag()
    where_clause = sql.and_(
        _TABLE.c.etag == if_match_etag,
        _TABLE.c.id == t_id
    )
    query = _TABLE.update().returning(*_TABLE.columns).\
        where(where_clause).values(**values)

    result = flask.g.db_conn.execute(query)
    if not result.rowcount:
        raise dci_exc.DCIConflict('Team', t_id)

    return flask.Response(
        json.dumps({'team': result.fetchone()}), 200,
        headers={'ETag': values['etag']},
        content_type='application/json'
    )


@api.route('/teams/<uuid:t_id>', methods=['DELETE'])
@decorators.login_required
def delete_team_by_id(user, t_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    v1_utils.verify_existence_and_get(t_id, _TABLE)

    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    with flask.g.db_conn.begin():
        values = {'state': 'archived'}
        where_clause = sql.and_(
            _TABLE.c.etag == if_match_etag,
            _TABLE.c.id == t_id
        )
        query = _TABLE.update().where(where_clause).values(**values)
        result = flask.g.db_conn.execute(query)

        if not result.rowcount:
            raise dci_exc.DCIDeleteConflict('Team', t_id)

        for model in [models.FILES, models.REMOTECIS, models.JOBS]:
            query = model.update().where(model.c.team_id == t_id).values(
                **values
            )
            flask.g.db_conn.execute(query)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/teams/purge', methods=['GET'])
@decorators.login_required
def get_to_purge_archived_teams(user):
    return base.get_to_purge_archived_resources(user, _TABLE)


@api.route('/teams/purge', methods=['POST'])
@decorators.login_required
def purge_archived_teams(user):
    return base.purge_archived_resources(user, _TABLE)
