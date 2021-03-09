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
import sqlalchemy.orm as sa_orm

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
from dci.db import declarative as d
from dci.db import embeds
from dci.db import models
from dci.db import models2

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

    try:
        t = models2.Team(**values)
        t_serialized = t.serialize()
        flask.g.session.add(t)
        flask.g.session.commit()
    except sa_exc.IntegrityError as ie:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message=str(ie), status_code=409)
    except Exception as e:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message=str(e))

    return flask.Response(
        json.dumps({'team': t_serialized}), 201,
        headers={'ETag': values['etag']}, content_type='application/json'
    )


@api.route('/teams', methods=['GET'])
@decorators.login_required
def get_all_teams(user):
    args = check_and_get_args(flask.request.args.to_dict())

    q = flask.g.session.query(models2.Team)

    if user.is_not_super_admin() and user.is_not_epm() and user.is_not_read_only_user():
        q = q.filter(models2.Team.id.in_(user.teams_ids))

    q = q.filter(models2.Team.state != 'archived').\
        filter(models2.Team.state != 'archived').\
        options(sa_orm.joinedload('topics')).\
        options(sa_orm.joinedload('remotecis'))
    q = d.handle_args(q, models2.Team, args)
    nb_teams = q.count()

    q = d.handle_pagination(q, args)
    teams = q.all()
    teams = list(map(lambda t: t.serialize(), teams))

    return flask.jsonify({'teams': teams, '_meta': {'count': nb_teams}})


@api.route('/teams/<uuid:t_id>', methods=['GET'])
@decorators.login_required
def get_team_by_id(user, t_id):
    v1_utils.verify_existence_and_get(t_id, _TABLE)
    if user.is_not_in_team(t_id) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    t = flask.g.session.query(models2.Team).\
        filter(models2.Team.state != 'archived').\
        filter(models2.Team.id == t_id).\
        options(sa_orm.joinedload('remotecis')).\
        options(sa_orm.joinedload('topics')).one()
    if not t:
        raise dci_exc.DCIException(message="team not found", status_code=404)

    return flask.Response(
        json.dumps({'team': t.serialize()}), 200, headers={'ETag': t.etag},
        content_type='application/json')


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
    for k in ('topics', 'remotecis'):
        try:
            values.pop(k)
        except KeyError:
            pass

    if user.is_not_super_admin() and user.is_not_epm():
        raise dci_exc.Unauthorized()

    v1_utils.verify_existence_and_get(t_id, _TABLE)

    values['etag'] = utils.gen_etag()

    updated_team = flask.g.session.query(models2.Team).\
        filter(models2.Team.id == t_id).\
        filter(models2.Team.etag == if_match_etag).\
        update(values)
    flask.g.session.commit()

    if not updated_team:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message="update failed, either team not found or etag not matched", status_code=409)

    t = flask.g.session.query(models2.Team).filter(models2.Team.id == t_id).one()
    if not t:
        raise dci_exc.DCIException(message="unable to return team", status_code=400)

    return flask.Response(
        json.dumps({'team': t.serialize()}), 200, headers={'ETag': values['etag']},
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

    deleted_team = flask.g.session.query(models2.Team).\
        filter(models2.Team.id == t_id).\
        filter(models2.Team.etag == if_match_etag).\
        update({'state': 'archived'})
    flask.g.session.commit()

    if not deleted_team:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message="delete failed, either team already deleted or etag not matched", status_code=409)

    # will use models2 when FILES and JOBS will be done in models2
    for model in [models.FILES, models.REMOTECIS, models.JOBS]:
        query = model.update().where(model.c.team_id == t_id).values(state='archived')
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
