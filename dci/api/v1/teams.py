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
from sqlalchemy import exc as sa_exc
from sqlalchemy import sql

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import remotecis
from dci.api.v1 import tests
from dci.api.v1 import utils as v1_utils
from dci import auth
from dci.common import audits
from dci.common import exceptions as dci_exc
from dci.common import schemas
from dci.common import utils
from dci.db import embeds
from dci.db import models
from dci.db.orm import dci_orm
from dci.db.orm import orm_utils

# associate column names with the corresponding SA Column object
_TABLE = models.TEAMS
_VALID_EMBED = embeds.teams()
_T_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)


@api.route('/teams', methods=['POST'])
@auth.requires_auth
@audits.log
def create_teams(user):
    created_at, updated_at = utils.get_dates(user)
    values = schemas.team.post(flask.request.json)

    if not user.is_super_admin():
        raise auth.UNAUTHORIZED

    values.update({
        'id': utils.gen_uuid(),
        'created_at': created_at,
        'updated_at': updated_at,
        'etag': utils.gen_etag()
    })
    session = flask.g.db

    new_team = dci_orm.Team()

    for key, value in values.iteritems():
        setattr(new_team, key, value)

    try:
        session.add(new_team)
        session.commit()
        session.flush()
    except sa_exc.IntegrityError:
        session.rollback()
        raise dci_exc.DCICreationConflict(_TABLE.name, 'name')

    return flask.Response(
        json.dumps({'team': new_team.serialize}), 201,
        headers={'ETag': new_team.etag}, content_type='application/json'
    )


@api.route('/teams', methods=['GET'])
@auth.requires_auth
def get_all_teams(user):
    args = schemas.args(flask.request.args.to_dict())

    session = flask.g.db
    query = session.query(dci_orm.Team)

    if not user.is_super_admin():
        query = query.filter(dci_orm.Team.id == user.team_id)

    query = orm_utils.std_query(dci_orm.Team, query, args)

    return flask.jsonify({'teams': [i.serialize for i in query.all()],
                          '_meta': {'count': query.count()}})


@api.route('/teams/<uuid:t_id>', methods=['GET'])
@auth.requires_auth
def get_team_by_id_or_name(user, t_id):
    args = schemas.args(flask.request.args.to_dict())

    if not(user.is_super_admin() or user.team_id == t_id):
        raise auth.UNAUTHORIZED

    session = flask.g.db
    query = session.query(dci_orm.Team)

    query = query.filter(dci_orm.Team.state != 'archived')
    query = query.filter(dci_orm.Team.id == t_id)

    team = query.first()

    res = flask.jsonify({'team': team.serialize})
    res.headers.add_header('ETag', team.etag)
    return res


@api.route('/teams/<uuid:team_id>/remotecis', methods=['GET'])
@auth.requires_auth
def get_remotecis_by_team(user, team_id):
    team = v1_utils.verify_existence_and_get(team_id, _TABLE)
    return remotecis.get_all_remotecis(team['id'])


@api.route('/teams/<uuid:team_id>/tests', methods=['GET'])
@auth.requires_auth
def get_tests_by_team(user, team_id):
    team = v1_utils.verify_existence_and_get(team_id, _TABLE)
    return tests.get_all_tests(user, team['id'])


@api.route('/teams/<uuid:t_id>', methods=['PUT'])
@auth.requires_auth
def put_team(user, t_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    values = schemas.team.put(flask.request.json)

    if not(user.is_super_admin() or user.is_team_admin(uuid.UUID(t_id))):
        raise auth.UNAUTHORIZED

    session = flask.g.db

    pteam = session.query(dci_orm.Team).get(t_id)

    if not pteam.etag == if_match_etag:
        raise dci_exc.DCIConflict('Team', t_id)
    pteam.etag = utils.gen_etag()

    for key, value in values.iteritems():
        setattr(pteam, key, value)

    try:
        session.commit()
        session.flush()
    except:
        session.rollaback()
        raise dci_exc.DCIConflict('Team', t_id)

    return flask.Response(None, 204, headers={'ETag': pteam.etag},
                          content_type='application/json')


@api.route('/teams/<uuid:t_id>', methods=['DELETE'])
@auth.requires_auth
def delete_team_by_id_or_name(user, t_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    if not user.is_super_admin():
        raise auth.UNAUTHORIZED

    session = flask.g.db

    dteam = session.query(dci_orm.Team).get(t_id)

    if not duser.etag == if_match_etag:
        raise dci_exc.DCIDeleteConflict('Team', t_id)

    duser.state = 'archived'
    try:
        session.commit()
        session.flush()
    except:
        session.rollback()
        raise dci_exc.DCIDeleteConflict('Team', t_id)

    return flask.Response(None, 204, content_type='application/json')


@api.route('/teams/purge', methods=['GET'])
@auth.requires_auth
def get_to_purge_archived_teams(user):
    return base.get_to_purge_archived_resources(user, _TABLE)


@api.route('/teams/purge', methods=['POST'])
@auth.requires_auth
def purge_archived_teams(user):
    return base.purge_archived_resources(user, _TABLE)
