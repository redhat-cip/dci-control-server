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
import sqlalchemy.orm as sa_orm

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import utils as v1_utils
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common.schemas import (
    check_json_is_valid,
    clean_json_with_schema,
    create_remoteci_schema,
    update_remoteci_schema,
    check_and_get_args,
)

from dci.common import signature
from dci.common import utils
from dci.db import declarative as d
from dci.db import models2


@api.route("/remotecis", methods=["POST"])
@decorators.login_required
def create_remotecis(user):
    values = flask.request.json
    check_json_is_valid(create_remoteci_schema, values)
    values.update(v1_utils.common_values_dict())
    values.update(
        {
            # XXX(fc): this should be populated as a default value from the
            # model, but we don't return values from the database :(
            "api_secret": signature.gen_secret(),
            "data": values.get("data", {}),
        }
    )

    if user.is_not_in_team(values["team_id"]) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    remoteci = base.create_resource_orm(models2.Remoteci, values)

    return flask.Response(
        json.dumps({"remoteci": remoteci}),
        201,
        headers={"ETag": values["etag"]},
        content_type="application/json",
    )


@api.route("/remotecis", methods=["GET"])
@decorators.login_required
def get_all_remotecis(user, t_id=None):
    args = check_and_get_args(flask.request.args.to_dict())

    q = flask.g.session.query(models2.Remoteci)
    if user.is_not_super_admin() and user.is_not_epm() and user.is_not_read_only_user():
        q = q.filter(models2.Remoteci.team_id.in_(user.teams_ids))

    if t_id is not None:
        q = q.filter(models2.Remoteci.team_id == t_id)

    q = (
        q.filter(models2.Remoteci.state != "archived")
        .options(sa_orm.joinedload("team", innerjoin=True))
        .options(sa_orm.selectinload("users"))
    )

    q = d.handle_args(q, models2.Remoteci, args)
    nb_remotecis = q.count()

    q = d.handle_pagination(q, args)
    remotecis = q.all()
    remotecis = list(map(lambda r: r.serialize(), remotecis))

    return flask.jsonify({"remotecis": remotecis, "_meta": {"count": nb_remotecis}})


@api.route("/remotecis/<uuid:remoteci_id>", methods=["GET"])
@decorators.login_required
def get_remoteci_by_id(user, remoteci_id):
    r = base.get_resource_orm(
        models2.Remoteci,
        remoteci_id,
        options=[
            sa_orm.joinedload("team", innerjoin=True),
            sa_orm.selectinload("users"),
        ],
    )
    if user.is_not_in_team(r.team_id) and user.is_not_read_only_user():
        raise dci_exc.Unauthorized()

    return flask.Response(
        json.dumps({"remoteci": r.serialize()}),
        200,
        headers={"ETag": r.etag},
        content_type="application/json",
    )


@api.route("/remotecis/<uuid:remoteci_id>", methods=["PUT"])
@decorators.login_required
def put_remoteci(user, remoteci_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    values = clean_json_with_schema(update_remoteci_schema, flask.request.json)

    remoteci = base.get_resource_orm(models2.Remoteci, remoteci_id, if_match_etag)

    if user.is_not_in_team(remoteci.team_id) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    base.update_resource_orm(remoteci, values)

    remoteci = base.get_resource_orm(models2.Remoteci, remoteci_id)

    return flask.Response(
        json.dumps({"remoteci": remoteci.serialize(ignore_columns=["api_secret"])}),
        200,
        headers={"ETag": remoteci.etag},
        content_type="application/json",
    )


@api.route("/remotecis/<uuid:remoteci_id>", methods=["DELETE"])
@decorators.login_required
def delete_remoteci_by_id(user, remoteci_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    remoteci = base.get_resource_orm(models2.Remoteci, remoteci_id, if_match_etag)

    if user.is_not_in_team(remoteci.team_id) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    base.update_resource_orm(remoteci, {"state": "archived", "users": []})

    try:
        flask.g.session.query(models2.Job).filter(
            models2.Job.remoteci_id == remoteci_id
        ).update({"state": "archived"})
        flask.g.session.commit()
    except Exception as e:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message=str(e), status_code=409)

    return flask.Response(None, 204, content_type="application/json")


# TODO (gvincent): this is already provided by /remotecis/<uuid:remoteci_id> and will be removed
@api.route("/remotecis/<uuid:remoteci_id>/data", methods=["GET"])
@decorators.login_required
def get_remoteci_data(user, remoteci_id):
    r = base.get_resource_orm(models2.Remoteci, remoteci_id)

    if user.is_not_in_team(r.team_id) and user.is_not_read_only_user():
        raise dci_exc.Unauthorized()

    remoteci_data = r.data

    if "keys" in "keys" in flask.request.args:
        keys = flask.request.args.get("keys").split(",")
        remoteci_data = {k: remoteci_data[k] for k in keys if k in remoteci_data}

    return flask.jsonify(remoteci_data)


@api.route("/remotecis/<uuid:remoteci_id>/users", methods=["POST"])
@decorators.login_required
def add_user_to_remoteci(user, remoteci_id):
    r = base.get_resource_orm(
        models2.Remoteci, remoteci_id, options=[sa_orm.selectinload("users")]
    )
    u = base.get_resource_orm(models2.User, user.id)

    if user.is_not_in_team(r.team_id) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    try:
        r.users.append(u)
        flask.g.session.add(r)
        flask.g.session.commit()
    except sa_exc.IntegrityError:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message="conflict when adding user", status_code=409)

    result = json.dumps({"user_id": user.id, "remoteci_id": r.id})
    return flask.Response(result, 201, content_type="application/json")


# TODO (gvincent): this is already provided by /remotecis/<uuid:remoteci_id> and will be removed
@api.route("/remotecis/<uuid:remoteci_id>/users", methods=["GET"])
@decorators.login_required
def get_all_users_from_remotecis(user, remoteci_id):
    r = base.get_resource_orm(
        models2.Remoteci, remoteci_id, options=[sa_orm.selectinload("users")]
    )
    if user.is_not_in_team(r.team_id) and user.is_not_epm():
        raise dci_exc.Unauthorized()
    users = r.serialize()["users"]
    res = flask.jsonify({"users": users, "_meta": {"count": len(users)}})
    return res


@api.route("/remotecis/<uuid:remoteci_id>/users/<uuid:u_id>", methods=["DELETE"])
@decorators.login_required
def delete_user_from_remoteci(user, remoteci_id, u_id):
    r = base.get_resource_orm(
        models2.Remoteci, remoteci_id, options=[sa_orm.selectinload("users")]
    )
    u = base.get_resource_orm(models2.User, u_id)

    if user.is_not_in_team(r.team_id) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    try:
        r.users.remove(u)
        flask.g.session.add(r)
        flask.g.session.commit()
    except sa_exc.IntegrityError:
        flask.g.session.rollback()
        raise dci_exc.DCIException(
            message="conflict when removing user", status_code=409
        )

    return flask.Response(None, 204, content_type="application/json")


@api.route("/remotecis/purge", methods=["GET"])
@decorators.login_required
def get_remotecis_to_purge(user):
    return base.get_resources_to_purge_orm(user, models2.Remoteci)


@api.route("/remotecis/purge", methods=["POST"])
@decorators.login_required
def purge_archived_remotecis(user):
    return base.purge_archived_resources_orm(user, models2.Remoteci)


@api.route("/remotecis/<uuid:remoteci_id>/api_secret", methods=["PUT"])
@decorators.login_required
def put_api_secret_remoteci(user, remoteci_id):
    utils.check_and_get_etag(flask.request.headers)
    remoteci = base.get_resource_orm(models2.Remoteci, remoteci_id)

    if not user.is_in_team(remoteci.team_id):
        raise dci_exc.Unauthorized()

    base.update_resource_orm(remoteci, {"api_secret": signature.gen_secret()})

    remoteci = base.get_resource_orm(models2.Remoteci, remoteci_id)
    return flask.Response(
        json.dumps({"remoteci": remoteci.serialize()}),
        200,
        headers={"ETag": remoteci.etag},
        content_type="application/json",
    )
