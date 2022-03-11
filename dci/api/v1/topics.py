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
from sqlalchemy import sql

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import components
from dci.api.v1 import export_control
from dci.api.v1 import utils as v1_utils
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common.schemas import (
    check_json_is_valid,
    clean_json_with_schema,
    create_topic_schema,
    update_topic_schema,
    check_and_get_args,
    add_team_to_topic_schema,
)
from dci.common import utils
from dci.db import declarative as d
from dci.db import models
from dci.db import models2

# associate column names with the corresponding SA Column object
_TABLE = models.TOPICS


@api.route("/topics", methods=["POST"])
@decorators.login_required
def create_topics(user):
    values = flask.request.json
    check_json_is_valid(create_topic_schema, values)
    values.update(v1_utils.common_values_dict())

    if user.is_not_super_admin() and user.is_not_epm() and user.is_not_feeder():
        raise dci_exc.Unauthorized()

    values["component_types"] = [type.lower() for type in values["component_types"]]

    t = base.create_resource_orm(models2.Topic, values)

    return flask.Response(
        json.dumps({"topic": t}),
        201,
        headers={"ETag": values["etag"]},
        content_type="application/json",
    )


@api.route("/topics/<uuid:topic_id>", methods=["GET"])
@decorators.login_required
def get_topic_by_id(user, topic_id):
    topic = base.get_resource_orm(
        models2.Topic,
        topic_id,
        options=[
            sa_orm.selectinload("teams"),
            sa_orm.joinedload("product", innerjoin=True),
            sa_orm.selectinload("next_topic"),
        ],
    )
    topic_serialized = topic.serialize()

    if user.is_not_super_admin() and user.is_not_epm() and user.is_not_feeder():
        if not user.is_read_only_user():
            export_control.verify_access_to_topic(user, topic)
            topic_serialized["teams"] = []

    return flask.Response(
        json.dumps({"topic": topic_serialized}),
        200,
        headers={"ETag": topic.etag},
        content_type="application/json",
    )


@api.route("/topics", methods=["GET"])
@decorators.login_required
def get_all_topics(user):
    def _get_user_product_ids():
        q = flask.g.session.query(models2.Product).filter(
            models2.Product.state != "archived"
        )
        _JPT = models2.JOIN_PRODUCTS_TEAMS
        q = q.join(
            _JPT,
            sql.and_(
                _JPT.c.product_id == models2.Product.id,
                _JPT.c.team_id.in_(user.teams_ids),
            ),
        )
        return [p.id for p in q.all()]

    args = check_and_get_args(flask.request.args.to_dict())
    q = (
        flask.g.session.query(models2.Topic)
        .filter(models2.Topic.state != "archived")
        .options(sa_orm.joinedload("product", innerjoin=True))
        .options(sa_orm.selectinload("next_topic"))
    )

    if user.is_not_super_admin() and user.is_not_read_only_user() and user.is_not_epm():
        product_ids = _get_user_product_ids()
        q = q.filter(models2.Topic.product_id.in_(product_ids))
        q = q.filter(
            sql.or_(
                models2.Topic.export_control == True,  # noqa
                models2.Topic.id.in_(v1_utils.user_topic_ids(user)),
            )
        )
    else:
        q = q.options(sa_orm.selectinload("teams"))

    q = d.handle_args(q, models2.Topic, args)
    nb_topics = q.count()
    q = d.handle_pagination(q, args)

    topics = q.all()
    topics = list(map(lambda t: t.serialize(), topics))

    return flask.jsonify({"topics": topics, "_meta": {"count": nb_topics}})


@api.route("/topics/<uuid:topic_id>", methods=["PUT"])
@decorators.login_required
def put_topic(user, topic_id):
    if user.is_not_super_admin() and user.is_not_epm() and user.is_not_feeder():
        raise dci_exc.Unauthorized()

    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    topic = base.get_resource_orm(models2.Topic, topic_id, if_match_etag)
    values = clean_json_with_schema(update_topic_schema, flask.request.json)

    if "component_types" in values:
        values["component_types"] = [type.lower() for type in values["component_types"]]

    base.update_resource_orm(topic, values)
    topic = base.get_resource_orm(models2.Topic, topic_id)

    return flask.Response(
        json.dumps({"topic": topic.serialize()}),
        200,
        headers={"ETag": topic.etag},
        content_type="application/json",
    )


@api.route("/topics/<uuid:topic_id>", methods=["DELETE"])
@decorators.login_required
def delete_topic_by_id(user, topic_id):
    if user.is_not_super_admin() and user.is_not_epm():
        raise dci_exc.Unauthorized()

    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    topic = base.get_resource_orm(models2.Topic, topic_id, if_match_etag)

    try:
        topic.state = "archived"
        flask.g.session.query(models2.Component).filter(
            models2.Component.topic_id == topic_id
        ).update({"state": "archived"}, synchronize_session=False)
        flask.g.session.commit()
    except Exception as e:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message=str(e), status_code=409)

    return flask.Response(None, 204, content_type="application/json")


# GET components
@api.route("/topics/<uuid:topic_id>/components", methods=["GET"])
@decorators.login_required
def get_topics_components(user, topic_id):
    topic = base.get_resource_orm(models2.Topic, topic_id)
    export_control.verify_access_to_topic(user, topic)
    return components.get_all_components(user, topic_id=topic_id)


# teams set apis
@api.route("/topics/<uuid:topic_id>/teams", methods=["POST"])
@decorators.login_required
def add_team_to_topic(user, topic_id):
    if user.is_not_super_admin() and user.is_not_epm():
        raise dci_exc.Unauthorized()

    values = flask.request.json
    check_json_is_valid(add_team_to_topic_schema, values)
    team_id = values.get("team_id")

    topic = base.get_resource_orm(models2.Topic, topic_id)
    team = base.get_resource_orm(models2.Team, team_id)

    try:
        topic.teams.append(team)
        flask.g.session.add(topic)
        flask.g.session.commit()
    except sa_exc.IntegrityError:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message="conflict when adding team", status_code=409)

    result = json.dumps({"topic_id": topic.id, "team_id": team.id})
    return flask.Response(result, 201, content_type="application/json")


@api.route("/topics/<uuid:topic_id>/teams/<uuid:team_id>", methods=["DELETE"])
@decorators.login_required
def delete_team_from_topic(user, topic_id, team_id):
    if user.is_not_super_admin() and user.is_not_epm():
        raise dci_exc.Unauthorized()

    topic = base.get_resource_orm(models2.Topic, topic_id)
    team = base.get_resource_orm(models2.Team, team_id)

    try:
        topic.teams.remove(team)
        flask.g.session.add(topic)
        flask.g.session.commit()
    except sa_exc.IntegrityError:
        flask.g.session.rollback()
        raise dci_exc.DCIException(
            message="conflict when removing team", status_code=409
        )

    return flask.Response(None, 204, content_type="application/json")


# this is already provided by GET /topics/<uuid:topic_id> and will be removed
@api.route("/topics/<uuid:topic_id>/teams", methods=["GET"])
@decorators.login_required
def get_all_teams_from_topic(user, topic_id):
    topic = v1_utils.verify_existence_and_get(topic_id, _TABLE)

    if user.is_not_super_admin() and user.is_not_epm():
        raise dci_exc.Unauthorized()

    # Get all teams which belongs to a given topic
    JTT = models.JOINS_TOPICS_TEAMS
    query = (
        sql.select([models.TEAMS])
        .select_from(JTT.join(models.TEAMS))
        .where(JTT.c.topic_id == topic["id"])
    )
    rows = flask.g.db_conn.execute(query)

    return flask.jsonify({"teams": rows, "_meta": {"count": rows.rowcount}})


@api.route("/topics/purge", methods=["GET"])
@decorators.login_required
def get_to_purge_archived_topics(user):
    return base.get_to_purge_archived_resources(user, models2.Topic)


@api.route("/topics/purge", methods=["POST"])
@decorators.login_required
def purge_archived_topics(user):
    return base.purge_archived_resources(user, models2.Topic)
