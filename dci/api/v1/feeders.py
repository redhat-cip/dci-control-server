# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Red Hat, Inc
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

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import utils as v1_utils
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common.schemas import (
    check_json_is_valid,
    clean_json_with_schema,
    create_feeder_schema,
    update_feeder_schema,
    check_and_get_args,
)
from dci.common import signature
from dci.common import utils

from dci.db import models2
from dci.db import declarative


@api.route("/feeders", methods=["POST"])
@decorators.login_required
def create_feeders(user):
    values = flask.request.json
    check_json_is_valid(create_feeder_schema, values)
    values.update(v1_utils.common_values_dict())

    if user.is_not_epm() and user.is_not_super_admin():
        raise dci_exc.Unauthorized()

    values.update(
        {
            # XXX(fc): this should be populated as a default value from the
            # model, but we don't return values from the database :(
            "api_secret": signature.gen_secret(),
            "data": values.get("data", {}),
        }
    )

    feeder = base.create_resource_orm(models2.Feeder, values)

    return flask.Response(
        json.dumps({"feeder": feeder}),
        201,
        headers={"ETag": values["etag"]},
        content_type="application/json",
    )


@api.route("/feeders", methods=["GET"])
@decorators.login_required
def get_all_feeders(user, t_id=None):
    args = check_and_get_args(flask.request.args.to_dict())

    query = flask.g.session.query(models2.Feeder)
    if user.is_not_super_admin() and user.is_not_epm():
        query = query.filter(models2.Feeder.team_id.in_(user.teams_ids))

    query = query.filter(models2.Feeder.state != "archived")
    query = declarative.handle_args(query, models2.Feeder, args)
    nb_feeders = query.count()
    query = declarative.handle_pagination(query, args)
    feeders = [feeder.serialize() for feeder in query.all()]

    return flask.jsonify({"feeders": feeders, "_meta": {"count": nb_feeders}})


@api.route("/feeders/<uuid:feeder_id>", methods=["GET"])
@decorators.login_required
def get_feeder_by_id(user, feeder_id):
    feeder = base.get_resource_orm(models2.Feeder, feeder_id)

    if user.is_not_in_team(feeder.team_id):
        raise dci_exc.Unauthorized()

    return flask.Response(
        json.dumps({"feeder": feeder.serialize()}),
        200,
        headers={"ETag": feeder.etag},
        content_type="application/json",
    )


@api.route("/feeders/<uuid:feeder_id>", methods=["PUT"])
@decorators.login_required
def put_feeder(user, feeder_id):
    # get If-Match header
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    values = clean_json_with_schema(update_feeder_schema, flask.request.json)

    feeder = base.get_resource_orm(models2.Feeder, feeder_id, if_match_etag)

    if user.is_not_in_team(feeder.team_id):
        raise dci_exc.Unauthorized()

    base.update_resource_orm(feeder, values)

    feeder = base.get_resource_orm(models2.Feeder, feeder_id)

    return flask.Response(
        json.dumps({"feeder": feeder.serialize(ignore_columns=["api_secret"])}),
        200,
        headers={"ETag": feeder.etag},
        content_type="application/json",
    )


@api.route("/feeders/<uuid:feeder_id>", methods=["DELETE"])
@decorators.login_required
def delete_feeder_by_id(user, feeder_id):
    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    feeder = base.get_resource_orm(models2.Feeder, feeder_id, if_match_etag)

    if user.is_not_in_team(feeder.team_id) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    base.update_resource_orm(feeder, {"state": "archived"})
    return flask.Response(None, 204, content_type="application/json")


@api.route("/feeders/purge", methods=["GET"])
@decorators.login_required
def get_feeders_to_purge(user):
    return base.get_resources_to_purge_orm(user, models2.Feeder)


@api.route("/feeders/purge", methods=["POST"])
@decorators.login_required
def purge_archived_feeders(user):
    return base.purge_archived_resources_orm(user, models2.Feeder)


@api.route("/feeders/<uuid:feeder_id>/api_secret", methods=["PUT"])
@decorators.login_required
def put_api_secret_feeder(user, feeder_id):
    utils.check_and_get_etag(flask.request.headers)
    feeder = base.get_resource_orm(models2.Feeder, feeder_id)

    if not user.is_in_team(feeder.team_id):
        raise dci_exc.Unauthorized()

    base.update_resource_orm(feeder, {"api_secret": signature.gen_secret()})

    feeder = base.get_resource_orm(models2.Feeder, feeder_id)
    return flask.Response(
        json.dumps({"feeder": feeder.serialize()}),
        200,
        headers={"ETag": feeder.etag},
        content_type="application/json",
    )
