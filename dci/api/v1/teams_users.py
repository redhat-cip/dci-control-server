# -*- coding: utf-8 -*-
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
from sqlalchemy import exc as sa_exc

from dci.api.v1 import api
from dci.api.v1 import base
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.db import models2


@api.route('/teams/<uuid:team_id>/users/<uuid:user_id>', methods=['POST'])
@decorators.login_required
def add_user_to_team(user, team_id, user_id):
    if (team_id == flask.g.team_admin_id or
        team_id == flask.g.team_redhat_id or
        team_id == flask.g.team_epm_id) and user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    if user.is_not_epm():
        raise dci_exc.Unauthorized()

    team = base.get_resource_orm(models2.Team, team_id)
    user = base.get_resource_orm(models2.User, user_id)

    try:
        team.users.append(user)
        flask.g.session.add(team)
        flask.g.session.commit()
    except sa_exc.IntegrityError:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message="conflict when adding team", status_code=409)

    return flask.Response(None, 201, content_type='application/json')


@api.route('/teams/<uuid:team_id>/users', methods=['GET'])
@decorators.login_required
def get_users_from_team(user, team_id):
    if user.is_not_epm() and user.is_not_in_team(team_id):
        raise dci_exc.Unauthorized()
    team = base.get_resource_orm(models2.Team, team_id)
    team_users = [u.serialize() for u in team.users]

    return flask.jsonify({'users': team_users, '_meta': {'count': len(team_users)}})


@api.route('/users/<uuid:user_id>/teams', methods=['GET'])
@decorators.login_required
def get_teams_of_user(user, user_id):
    if user.is_not_super_admin() and user.id != user_id and user.is_not_epm():
        raise dci_exc.Unauthorized()

    user = base.get_resource_orm(models2.User, user_id)
    user_teams = [t.serialize() for t in user.team]

    return flask.jsonify({'teams': user_teams, '_meta': {'count': len(user_teams)}})


@api.route('/teams/<uuid:team_id>/users/<uuid:user_id>', methods=['DELETE'])
@decorators.login_required
def remove_user_from_team(user, team_id, user_id):

    if user.is_not_super_admin() and user.is_not_epm():
        raise dci_exc.Unauthorized()

    team = base.get_resource_orm(models2.Team, team_id)
    user = base.get_resource_orm(models2.User, user_id)

    try:
        team.users.remove(user)
        flask.g.session.add(team)
        flask.g.session.commit()
    except sa_exc.IntegrityError:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message="conflict when user from team", status_code=409)

    return flask.Response(None, 204, content_type='application/json')
