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
import re
from flask import json
from sqlalchemy import exc as sa_exc
import sqlalchemy.orm as sa_orm
from sqlalchemy import sql
from OpenSSL import crypto

from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import utils as v1_utils
from dci import dci_config
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
from dci.db import models
from dci.db import models2


# associate column names with the corresponding SA Column object
_TABLE = models.REMOTECIS
_R_COLUMNS = v1_utils.get_columns_name_with_objects(_TABLE)


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
        .options(sa_orm.joinedload("team"))
        .options(sa_orm.joinedload("users"))
    )

    q = d.handle_args(q, models2.Remoteci, args)
    nb_remotecis = q.count()

    q = d.handle_pagination(q, args)
    remotecis = q.all()
    remotecis = list(
        map(lambda r: r.serialize(ignore_columns=["keys", "cert_fp"]), remotecis)
    )

    return flask.jsonify({"remotecis": remotecis, "_meta": {"count": nb_remotecis}})


@api.route("/remotecis/<uuid:remoteci_id>", methods=["GET"])
@decorators.login_required
def get_remoteci_by_id(user, remoteci_id):
    v1_utils.verify_existence_and_get(remoteci_id, _TABLE)
    try:
        r = (
            flask.g.session.query(models2.Remoteci)
            .filter(models2.Remoteci.state != "archived")
            .filter(models2.Remoteci.id == remoteci_id)
            .options(sa_orm.joinedload("team"))
            .options(sa_orm.joinedload("users"))
            .one()
        )
    except sa_orm.exc.NoResultFound:
        raise dci_exc.DCIException(message="remoteci not found", status_code=404)

    if user.is_not_in_team(r.team_id) and user.is_not_read_only_user():
        raise dci_exc.Unauthorized()

    return flask.Response(
        json.dumps({"remoteci": r.serialize(ignore_columns=["keys", "cert_fp"])}),
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

    base.update_resource_orm(remoteci, {"state": "archived"})

    # will use models2 when FILES and JOBS will be done in models2
    for model in [models.JOBS]:
        values = {"state": "archived"}
        query = (
            model.update().where(model.c.remoteci_id == remoteci_id).values(**values)
        )
        flask.g.db_conn.execute(query)

    return flask.Response(None, 204, content_type="application/json")


# TODO (gvincent): this is already provided by /remotecis/<uuid:remoteci_id> and will be removed
@api.route("/remotecis/<uuid:remoteci_id>/data", methods=["GET"])
@decorators.login_required
def get_remoteci_data(user, remoteci_id):
    query = v1_utils.QueryBuilder(_TABLE, {}, _R_COLUMNS)

    if user.is_not_super_admin() and user.is_not_epm():
        query.add_extra_condition(_TABLE.c.team_id.in_(user.teams_ids))

    query.add_extra_condition(_TABLE.c.id == remoteci_id)
    row = query.execute(fetchone=True)

    if row is None:
        raise dci_exc.DCINotFound("RemoteCI", remoteci_id)

    remoteci_data = row["remotecis_data"]

    if "keys" in "keys" in flask.request.args:
        keys = flask.request.args.get("keys").split(",")
        remoteci_data = {k: remoteci_data[k] for k in keys if k in remoteci_data}

    return flask.jsonify(remoteci_data)


@api.route("/remotecis/<uuid:remoteci_id>/users", methods=["POST"])
@decorators.login_required
def add_user_to_remoteci(user, remoteci_id):
    try:
        r = (
            flask.g.session.query(models2.Remoteci)
            .filter(models2.Remoteci.state != "archived")
            .filter(models2.Remoteci.id == remoteci_id)
            .options(sa_orm.joinedload("users"))
            .one()
        )
    except sa_orm.exc.NoResultFound:
        raise dci_exc.DCIException(message="remoteci not found", status_code=404)

    try:
        u = (
            flask.g.session.query(models2.User)
            .filter(models2.User.state != "archived")
            .filter(models2.User.id == user.id)
            .one()
        )
    except sa_orm.exc.NoResultFound:
        raise dci_exc.DCIException(message="user not found", status_code=404)

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
    v1_utils.verify_existence_and_get(remoteci_id, _TABLE)

    JUR = models.JOIN_USER_REMOTECIS
    query = (
        sql.select([models.USERS])
        .select_from(JUR.join(models.USERS))
        .where(JUR.c.remoteci_id == remoteci_id)
    )
    rows = flask.g.db_conn.execute(query)

    res = flask.jsonify({"users": rows, "_meta": {"count": rows.rowcount}})
    return res


@api.route("/remotecis/<uuid:remoteci_id>/users/<uuid:u_id>", methods=["DELETE"])
@decorators.login_required
def delete_user_from_remoteci(user, remoteci_id, u_id):
    try:
        r = (
            flask.g.session.query(models2.Remoteci)
            .filter(models2.Remoteci.state != "archived")
            .filter(models2.Remoteci.id == remoteci_id)
            .options(sa_orm.joinedload("users"))
            .one()
        )
    except sa_orm.exc.NoResultFound:
        raise dci_exc.DCIException(message="remoteci not found", status_code=404)

    try:
        u = (
            flask.g.session.query(models2.User)
            .filter(models2.User.state != "archived")
            .filter(models2.User.id == u_id)
            .one()
        )
    except sa_orm.exc.NoResultFound:
        raise dci_exc.DCIException(message="user not found", status_code=404)

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


@api.route("/remotecis/<uuid:remoteci_id>/keys", methods=["PUT"])
@decorators.login_required
def update_remoteci_keys(user, remoteci_id):
    _CAKEY = dci_config.CONFIG["CA_KEY"]
    _CACERT = dci_config.CONFIG["CA_CERT"]

    if_match_etag = utils.check_and_get_etag(flask.request.headers)
    key, cert = v1_utils.get_key_and_cert_signed(_CAKEY, _CACERT)

    remoteci = base.get_resource_orm(models2.Remoteci, remoteci_id, if_match_etag)

    if user.is_not_in_team(remoteci.team_id) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    base.update_resource_orm(
        remoteci,
        {"cert_fp": re.sub(":", "", cert.digest("sha1").decode("utf-8")).lower()},
    )

    return flask.Response(
        json.dumps(
            {
                "keys": {
                    "key": crypto.dump_privatekey(crypto.FILETYPE_PEM, key).decode(
                        "utf-8"
                    ),
                    "cert": crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode(
                        "utf-8"
                    ),
                }
            }
        ),
        201,
        content_type="application/json",
    )
