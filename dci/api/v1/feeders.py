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
from sqlalchemy import exc
from sqlalchemy import orm

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

from dci.db import models
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

    try:
        feeder = models2.Feeders(**values)
        feeder_serialized = feeder.serialize()
        flask.g.session.add(feeder)
        flask.g.session.commit()
    except exc.IntegrityError as ie:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message=str(ie), status_code=409)
    except Exception as e:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message=str(e))

    return flask.Response(
        json.dumps({"feeder": feeder_serialized}),
        201,
        headers={"ETag": values["etag"]},
        content_type="application/json",
    )


@api.route("/feeders", methods=["GET"])
@decorators.login_required
def get_all_feeders(user, t_id=None):
    args = check_and_get_args(flask.request.args.to_dict())

    query = flask.g.session.query(models2.Feeders)
    if user.is_not_super_admin() and user.is_not_epm():
        query = query.filter(models2.Feeders.team_id.in_(user.teams_ids))

    query = query.filter(models2.Feeders.state != "archived")

    nb_feeders = query.count()

    query = declarative.handle_args(query, models2.Feeders, args)

    feeders = [feeder.serialize() for feeder in query.all()]

    return flask.jsonify({"feeders": feeders, "_meta": {"count": nb_feeders}})


@api.route("/feeders/<uuid:feeder_id>", methods=["GET"])
@decorators.login_required
def get_feeder_by_id(user, feeder_id):
    try:
        feeder = (
            flask.g.session.query(models2.Feeders)
            .filter(models2.Feeders.state != "archived")
            .filter(models2.Feeders.id == feeder_id)
            .one()
        )
    except orm.exc.NoResultFound:
        raise dci_exc.DCIException(message="feeder not found", status_code=404)

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

    try:
        feeder = (
            flask.g.session.query(models2.Feeders)
            .filter(models2.Feeders.state != "archived")
            .filter(models2.Feeders.id == feeder_id)
            .one()
        )
    except orm.exc.NoResultFound:
        raise dci_exc.DCIException(message="feeder not found", status_code=404)

    if feeder.etag != if_match_etag:
        raise dci_exc.DCIException(message="etag not matched", status_code=409)

    if user.is_not_in_team(feeder.team_id):
        raise dci_exc.Unauthorized()

    values["etag"] = utils.gen_etag()

    for k, v in values.items():
        setattr(feeder, k, v)

    try:
        flask.g.session.commit()
    except Exception as e:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message=str(e), status_code=409)

    try:
        feeder = (
            flask.g.session.query(models2.Feeders)
            .filter(models2.Feeders.state != "archived")
            .filter(models2.Feeders.id == feeder_id)
            .one()
        )
    except orm.exc.NoResultFound:
        raise dci_exc.DCIException(message="feeder not found", status_code=404)

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
    try:
        feeder = (
            flask.g.session.query(models2.Feeders)
            .filter(models2.Feeders.state != "archived")
            .filter(models2.Feeders.id == feeder_id)
            .filter(models2.Feeders.etag == if_match_etag)
            .one()
        )
    except orm.exc.NoResultFound:
        raise dci_exc.DCIException(message="feeder not found", status_code=404)

    if user.is_not_in_team(feeder.team_id) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    deleted_feeder = (
        flask.g.session.query(models2.Feeders)
        .filter(models2.Feeders.id == feeder_id)
        .update({"state": "archived"})
    )
    flask.g.session.commit()

    if not deleted_feeder:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message="delete failed, check etag", status_code=409)

    return flask.Response(None, 204, content_type="application/json")


@api.route("/feeders/purge", methods=["GET"])
@decorators.login_required
def get_to_purge_archived_feeders(user):
    return base.get_to_purge_archived_resources(user, models.FEEDERS)


@api.route("/feeders/purge", methods=["POST"])
@decorators.login_required
def purge_archived_feeders(user):
    return base.purge_archived_resources(user, models.FEEDERS)


@api.route("/feeders/<uuid:f_id>/api_secret", methods=["PUT"])
@decorators.login_required
def put_api_secret_feeder(user, f_id):
    utils.check_and_get_etag(flask.request.headers)
    feeder = v1_utils.verify_existence_and_get(f_id, models.FEEDERS)
    if not user.is_in_team(feeder["team_id"]):
        raise dci_exc.Unauthorized()

    return base.refresh_api_secret(user, feeder, models.FEEDERS)
