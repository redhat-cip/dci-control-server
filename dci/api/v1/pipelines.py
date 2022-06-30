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
from flask import json
import logging

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import utils as v1_utils
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common.schemas import (
    check_json_is_valid,
    clean_json_with_schema,
    create_pipeline_schema,
    update_pipeline_schema,
    check_and_get_args,
)
from dci.common import utils
from dci.db import declarative
from dci.db import models2
import sqlalchemy.orm as sa_orm


@api.route("/pipelines", methods=["POST"])
@decorators.login_required
def create_pipeline(user):
    values = flask.request.json
    check_json_is_valid(create_pipeline_schema, values)
    values.update(v1_utils.common_values_dict())

    if not user.is_in_team(values["team_id"]):
        raise dci_exc.Unauthorized()

    created_pipeline = base.create_resource_orm(models2.Pipeline, values)
    result = json.dumps({"pipeline": created_pipeline})

    return flask.Response(result, 201, content_type="application/json")


@api.route("/pipelines/<uuid:p_id>", methods=["GET"])
@decorators.login_required
def get_pipeline_by_id(user, p_id):
    p = base.get_resource_orm(
        models2.Pipeline,
        p_id,
        options=[sa_orm.selectinload("team")],
    )

    if user.is_not_super_admin() and user.is_not_read_only_user() and user.is_not_epm():
        if p.team_id not in user.teams_ids:
            raise dci_exc.Unauthorized()

    return flask.Response(
        json.dumps({"pipeline": p.serialize()}),
        200,
        content_type="application/json",
    )


@api.route("/pipelines", methods=["GET"])
@decorators.login_required
def get_pipelines(user):
    args = check_and_get_args(flask.request.args.to_dict())

    query = flask.g.session.query(models2.Pipeline)

    if user.is_not_super_admin() and user.is_not_read_only_user() and user.is_not_epm():
        query = query.filter(models2.Pipeline.team_id.in_(user.teams_ids))
    query = query.filter(models2.Pipeline.state != "archived")
    query = query.from_self()
    query = declarative.handle_args(query, models2.Pipeline, args)
    query = query.options(sa_orm.joinedload("team", innerjoin=True))

    nb_pipelines = query.count()
    query = declarative.handle_pagination(query, args)

    pipelines = [j.serialize(ignore_columns=["data"]) for j in query.all()]

    return flask.jsonify({"pipelines": pipelines, "_meta": {"count": nb_pipelines}})


@api.route("/pipelines/<uuid:p_id>/jobs", methods=["GET"])
@decorators.login_required
def get_jobs_from_pipeline(user, p_id):
    p = base.get_resource_orm(models2.Pipeline, p_id)

    query = flask.g.session.query(models2.Job)

    if user.is_not_super_admin() and user.is_not_read_only_user() and user.is_not_epm():
        if p.team_id not in user.teams_ids:
            raise dci_exc.Unauthorized()
        query = query.filter(models2.Job.team_id.in_(user.teams_ids))

    query = query.filter(models2.Job.pipeline_id == p.id)
    query = query.filter(models2.Job.state != "archived")
    query = query.order_by(models2.Job.created_at.asc())
    query = (
        query.options(sa_orm.selectinload("results"))
        .options(sa_orm.joinedload("remoteci", innerjoin=True))
        .options(sa_orm.selectinload("components"))
        .options(sa_orm.joinedload("team", innerjoin=True))
    )

    jobs = [j.serialize() for j in query.all()]

    return flask.jsonify({"jobs": jobs, "_meta": {"count": len(jobs)}})


@api.route("/pipelines/<uuid:p_id>", methods=["PUT"])
@decorators.login_required
def update_pipeline_by_id(user, p_id):
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    values = clean_json_with_schema(update_pipeline_schema, flask.request.json)

    p = base.get_resource_orm(models2.Pipeline, p_id, if_match_etag)

    if user.is_not_in_team(p.team_id) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    base.update_resource_orm(p, values)
    p = base.get_resource_orm(models2.Pipeline, p_id)

    return flask.Response(
        json.dumps({"pipeline": p.serialize()}),
        200,
        headers={"ETag": p.etag},
        content_type="application/json",
    )


@api.route("/pipelines/<uuid:p_id>", methods=["DELETE"])
@decorators.login_required
def delete_pipeline_by_id(user, p_id):
    if_match_etag = utils.check_and_get_etag(flask.request.headers)

    p = base.get_resource_orm(models2.Pipeline, p_id, if_match_etag)

    if (
        user.is_not_in_team(p.team_id) or user.is_read_only_user()
    ) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    try:
        p.state = "archived"
        flask.g.session.add(p)
        flask.g.session.commit()
    except Exception as e:
        flask.g.session.rollback()
        logging.error("unable to delete pipeline %s: %s" % (p_id, str(e)))
        raise dci_exc.DCIException("unable to delete pipeline %s: %s" % (p_id, str(e)))

    return flask.Response(None, 204, content_type="application/json")
