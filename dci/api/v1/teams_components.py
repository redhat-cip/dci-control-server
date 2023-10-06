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
from sqlalchemy import exc as sa_exc

from dci.api.v1 import api
from dci.api.v1 import base
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common.schemas import check_json_is_valid, add_team_components_access
from dci.db import models2


@api.route(
    "/teams/<uuid:team_id>/permissions/components",
    methods=["POST"],
)
@decorators.login_required
def add_component_access_team(user, team_id):
    if user.is_not_epm() and user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    values = flask.request.json
    check_json_is_valid(add_team_components_access, values)

    if str(team_id) in values["teams_ids"]:
        values["teams_ids"].remove(str(team_id))

    team = base.get_resource_orm(models2.Team, team_id)

    try:
        for t_id in values["teams_ids"]:
            access_team = base.get_resource_orm(models2.Team, t_id)
            team.components_access_teams.append(access_team)
        flask.g.session.add(team)
        flask.g.session.commit()
    except sa_exc.IntegrityError:
        flask.g.session.rollback()
        raise dci_exc.DCIException(
            message="conflict when adding component access teams ids", status_code=409
        )

    return flask.Response(None, 201, content_type="application/json")


@api.route(
    "/teams/<uuid:team_id>/permissions/components",
    methods=["DELETE"],
)
@decorators.login_required
def remove_component_access_team(user, team_id):
    if user.is_not_super_admin() and user.is_not_epm():
        raise dci_exc.Unauthorized()

    values = flask.request.json
    check_json_is_valid(add_team_components_access, values)

    team = base.get_resource_orm(models2.Team, team_id)

    try:
        for t_id in values["teams_ids"]:
            access_team = base.get_resource_orm(models2.Team, t_id)
            team.components_access_teams.remove(access_team)
        flask.g.session.add(team)
        flask.g.session.commit()
    except sa_exc.IntegrityError:
        flask.g.session.rollback()
        raise dci_exc.DCIException(
            message="conflict when removing component access teams ids", status_code=409
        )

    return flask.Response(None, 204, content_type="application/json")


@api.route(
    "/teams/<uuid:team_id>/permissions/components",
    methods=["GET"],
)
@decorators.login_required
def get_component_access_team(user, team_id):
    if user.is_not_super_admin() and user.is_not_epm():
        raise dci_exc.Unauthorized()

    team = base.get_resource_orm(models2.Team, team_id)
    components_access_team = [t.serialize() for t in team.components_access_teams]

    return flask.jsonify(
        {
            "teams": components_access_team,
            "_meta": {"count": len(components_access_team)},
        }
    )
