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
from dci.api.v1 import utils as v1_utils
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common.schemas import (
    check_json_is_valid,
    clean_json_with_schema,
    create_team_schema,
    update_team_schema,
    check_and_get_args,
)
from dci.common import utils
from dci.db import declarative as d
from dci.db import models2


@api.route("/teams", methods=["POST"])
@decorators.login_required
@decorators.log
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
        json.dumps({"team": t_serialized}),
        201,
        headers={"ETag": values["etag"]},
        content_type="application/json",
    )


@api.route("/teams", methods=["GET"])
@decorators.login_required
def get_all_teams(user):
    args = check_and_get_args(flask.request.args.to_dict())

    q = flask.g.session.query(models2.Team)

    if user.is_not_super_admin() and user.is_not_epm() and user.is_not_read_only_user():
        q = q.filter(models2.Team.id.in_(user.teams_ids))

    q = q.filter(models2.Team.state != "archived").options(
        sa_orm.selectinload("remotecis")
    )
    q = d.handle_args(q, models2.Team, args)
    nb_teams = q.count()

    q = d.handle_pagination(q, args)
    teams = q.all()
    teams = list(map(lambda t: t.serialize(), teams))

    return flask.jsonify({"teams": teams, "_meta": {"count": nb_teams}})


@api.route("/teams/<uuid:t_id>", methods=["GET"])
@decorators.login_required
def get_team_by_id(user, t_id):
    base.get_resource_orm(models2.Team, t_id)
    if user.is_not_in_team(t_id) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    try:
        t = (
            flask.g.session.query(models2.Team)
            .filter(models2.Team.state != "archived")
            .filter(models2.Team.id == t_id)
            .options(sa_orm.selectinload("remotecis"))
            .one()
        )
    except sa_orm.exc.NoResultFound:
        raise dci_exc.DCIException(message="team not found", status_code=404)

    return flask.Response(
        json.dumps({"team": t.serialize()}),
        200,
        headers={"ETag": t.etag},
        content_type="application/json",
    )


@api.route("/teams/<uuid:team_id>/remotecis", methods=["GET"])
@decorators.login_required
def get_remotecis_by_team(user, team_id):
    if user.is_not_in_team(team_id) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    team = base.get_resource_orm(models2.Team, team_id)
    return remotecis.get_all_remotecis(team.id)


@api.route("/teams/<uuid:t_id>", methods=["PUT"])
@decorators.login_required
def put_team(user, t_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    values = clean_json_with_schema(update_team_schema, flask.request.json)

    if user.is_not_super_admin() and user.is_not_epm():
        raise dci_exc.Unauthorized()

    base.get_resource_orm(models2.Team, t_id)

    values["etag"] = utils.gen_etag()

    updated_team = (
        flask.g.session.query(models2.Team)
        .filter(models2.Team.id == t_id)
        .filter(models2.Team.etag == if_match_etag)
        .update(values)
    )
    flask.g.session.commit()

    if not updated_team:
        flask.g.session.rollback()
        raise dci_exc.DCIException(
            message="update failed, either team not found or etag not matched",
            status_code=409,
        )

    t = flask.g.session.query(models2.Team).filter(models2.Team.id == t_id).one()
    if not t:
        raise dci_exc.DCIException(message="unable to return team", status_code=400)

    return flask.Response(
        json.dumps({"team": t.serialize()}),
        200,
        headers={"ETag": values["etag"]},
        content_type="application/json",
    )


@api.route("/teams/<uuid:t_id>", methods=["DELETE"])
@decorators.login_required
def delete_team_by_id(user, t_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    base.get_resource_orm(models2.Team, t_id)

    if user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    deleted_team = (
        flask.g.session.query(models2.Team)
        .filter(models2.Team.id == t_id)
        .filter(models2.Team.etag == if_match_etag)
        .update({"state": "archived"})
    )
    flask.g.session.commit()

    if not deleted_team:
        flask.g.session.rollback()
        raise dci_exc.DCIException(
            message="delete failed, either team already deleted or etag not matched",
            status_code=409,
        )

    try:
        for model in [models2.File, models2.Remoteci, models2.Job]:
            flask.g.session.query(model).filter(model.team_id == t_id).update(
                {"state": "archived"}
            )
        flask.g.session.commit()
    except Exception as e:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message=str(e), status_code=409)

    return flask.Response(None, 204, content_type="application/json")


@api.route("/teams/purge", methods=["GET"])
@decorators.login_required
def get_to_purge_archived_teams(user):
    return base.get_to_purge_archived_resources(user, models2.Team)


@api.route("/teams/purge", methods=["POST"])
@decorators.login_required
def purge_archived_teams(user):
    return base.purge_archived_resources(user, models2.Team)
