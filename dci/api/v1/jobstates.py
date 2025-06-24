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

import datetime
from dci.common.time import get_job_duration

import flask
from flask import json

from dci.analytics import access_data_layer as a_d_l
from dci.api.v1 import api
from dci.api.v1 import base
from dci.api.v1 import jobs_events
from dci.api.v1 import notifications
from dci import decorators
from dci.common import exceptions as dci_exc
from dci.common.schemas import check_json_is_valid, jobstate_schema, check_and_get_args
from dci.common import utils
from dci.db import models2
from dci.db import declarative
import sqlalchemy.orm as sa_orm


def insert_jobstate(values):
    job_state = models2.Jobstate(
        id=utils.gen_uuid(),
        job_id=values["job_id"],
        status=values["status"],
        created_at=datetime.datetime.utcnow().isoformat(),
    )
    flask.g.session.add(job_state)
    flask.g.session.commit()


def serialize_job(job_id):
    job = base.get_resource_orm(
        models2.Job,
        job_id,
        options=[
            sa_orm.joinedload("topic", innerjoin=True),
            sa_orm.joinedload("remoteci", innerjoin=True),
            sa_orm.selectinload("components"),
            sa_orm.selectinload("results"),
        ],
    )
    return job.serialize()


@api.route("/jobstates", methods=["POST"])
@decorators.login_required
def create_jobstates(user):
    values = flask.request.json
    check_json_is_valid(jobstate_schema, values)
    values.update(
        {"id": utils.gen_uuid(), "created_at": datetime.datetime.utcnow().isoformat()}
    )

    # if one create a 'failed' jobstates and the current state is either
    # 'run' or 'pre-run' then set the job to 'error' state
    job_id = values.get("job_id")
    job = base.get_resource_orm(models2.Job, job_id)
    status = values.get("status")
    if status in ["failure", "error"]:
        if job.status in ["new", "pre-run"]:
            values["status"] = "error"

    created_js = base.create_resource_orm(models2.Jobstate, values)

    is_job_final_state = job.status in models2.FINAL_STATUSES

    # Update job status
    job.status = status
    job.duration = get_job_duration(job)

    try:
        flask.g.session.commit()
    except Exception as e:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message=str(e), status_code=409)

    # send notification in case of final jobstate status
    if status in models2.FINAL_STATUSES and not is_job_final_state:
        job_serialized = serialize_job(job_id)
        jobs_events.create_event(
            job_serialized["id"], values["status"], job_serialized["topic_id"]
        )
        notifications.job_dispatcher(job_serialized)
        job = a_d_l.get_job_by_id(flask.g.session, job_id)
        notifications.publish({"event": "job_finished", "job": job})

    result = json.dumps({"jobstate": created_js})
    return flask.Response(result, 201, content_type="application/json")


def get_all_jobstates(user, job_id):
    """Get all jobstates."""
    args = check_and_get_args(flask.request.args.to_dict())
    job = base.get_resource_orm(models2.Job, job_id)
    if user.is_not_super_admin() and user.is_not_read_only_user() and user.is_not_epm():
        if job.team_id not in user.teams_ids:
            raise dci_exc.Unauthorized()

    query = flask.g.session.query(models2.Jobstate)
    query = query.filter(models2.Jobstate.job_id == job_id).options(
        sa_orm.selectinload("files")
    )
    query = declarative.handle_args(query, models2.Jobstate, args)
    nb_jobstates = query.count()
    query = declarative.handle_pagination(query, args)

    jobstates = [js.serialize() for js in query.all()]

    return flask.jsonify({"jobstates": jobstates, "_meta": {"count": nb_jobstates}})


@api.route("/jobstates/<uuid:js_id>", methods=["GET"])
@decorators.login_required
def get_jobstate_by_id(user, js_id):
    js = base.get_resource_orm(
        models2.Jobstate, js_id, options=[sa_orm.selectinload("files")]
    )
    return flask.Response(
        json.dumps({"jobstate": js.serialize()}),
        200,
        content_type="application/json",
    )


@api.route("/jobstates/<uuid:js_id>", methods=["DELETE"])
@decorators.login_required
def delete_jobstate_by_id(user, js_id):
    jobstate = base.get_resource_orm(models2.Jobstate, js_id)
    job = base.get_resource_orm(models2.Job, jobstate.job_id)

    if user.is_not_in_team(job.team_id) and user.is_not_epm():
        raise dci_exc.Unauthorized()

    try:
        flask.g.session.delete(jobstate)
        flask.g.session.commit()
    except Exception as e:
        flask.g.session.rollback()
        raise dci_exc.DCIException(message=str(e), status_code=409)

    return flask.Response(None, 204, content_type="application/json")
